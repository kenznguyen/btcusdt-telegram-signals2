"""Pure, in-memory S1 synthetic measurement harness."""
from __future__ import annotations
import ast, hashlib, json, math, platform, re, sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "synthetic-contract-fixture/v1"
PURPOSE = "PARSER_CONTRACT_TEST_ONLY"
MEASUREMENT_DEFINITION_REVISION = "S1-MEASUREMENTS-V1"
D10_TYPES = frozenset({
    "SYNTHETIC_OBJECT", "SYNTHETIC_EVIDENCE", "SYNTHETIC_ISSUER_CLAIM",
    "SYNTHETIC_POLICY_CLAIM", "SYNTHETIC_INVENTORY_CLAIM",
    "SYNTHETIC_SENSITIVITY_CLAIM", "SYNTHETIC_HOLD_CLAIM",
    "SYNTHETIC_DEPENDENCY_CLAIM", "SYNTHETIC_COPY_LINEAGE_CLAIM",
    "SYNTHETIC_FRESHNESS_CLAIM", "SYNTHETIC_BINDING_CLAIM",
})
TOP_REQUIRED = frozenset({"schema_version","fixture_id","case_id","fixture_type","subject","purpose","claims"})
TOP_OPTIONAL = frozenset({"notes"})
SUBJECT_FIELDS = frozenset({"object_id","version_id","namespace"})
RESERVED = frozenset({"expected","oracle","assertion","test_result","expected_result"})
CASE_RE = re.compile(r"SYN-(?:0[1-9]|[12][0-9]|3[0-8])\Z")
FIXTURE_RE = re.compile(r"syn-fixture-[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
SYN_RE = re.compile(r"syn-[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z")
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")

class ContractError(ValueError): pass
class JSONObject(tuple): pass

@dataclass(frozen=True)
class ParseResult:
    value: Any | None
    reason_code: str | None
    duplicate_paths: tuple[str, ...] = ()

def _pairs(pairs): return JSONObject(pairs)
def _constant(_): raise ContractError("PARSE_NONFINITE_NUMBER")

def _unicode(value):
    if isinstance(value, str):
        if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise ContractError("PARSE_INVALID_UNICODE")
    elif isinstance(value, JSONObject):
        for key, child in value:
            _unicode(key); _unicode(child)
    elif isinstance(value, list):
        for child in value: _unicode(child)
    elif type(value) is float and not math.isfinite(value):
        raise ContractError("PARSE_NONFINITE_NUMBER")

def _duplicates(value, path="$"):
    found=[]
    if isinstance(value, JSONObject):
        seen=set()
        for key, child in value:
            child_path=f"{path}.{key}"
            if key in seen: found.append(child_path)
            seen.add(key); found.extend(_duplicates(child, child_path))
    elif isinstance(value, list):
        for i, child in enumerate(value): found.extend(_duplicates(child, f"{path}[{i}]"))
    return found

def parse_json_bytes(raw: bytes) -> ParseResult:
    if not isinstance(raw, bytes): return ParseResult(None,"INPUT_NOT_BYTES")
    try: decoded=raw.decode("utf-8","strict")
    except UnicodeDecodeError: return ParseResult(None,"PARSE_INVALID_UTF8")
    try:
        value=json.loads(decoded, object_pairs_hook=_pairs, parse_constant=_constant)
        _unicode(value)
    except ContractError as exc: return ParseResult(None,str(exc))
    except (json.JSONDecodeError, RecursionError, ValueError): return ParseResult(None,"PARSE_INVALID_JSON")
    duplicates=tuple(_duplicates(value))
    return ParseResult(value,"PARSE_DUPLICATE_KEY" if duplicates else None,duplicates)

def _dict(value): return {k:v for k,v in value}
def _plain(value):
    if isinstance(value,JSONObject): return {k:_plain(v) for k,v in value}
    if isinstance(value,list): return [_plain(v) for v in value]
    return value

def _synthetic(value): return type(value) is str and SYN_RE.fullmatch(value) is not None

def _claims_valid(claims, schema):
    if not isinstance(claims,JSONObject): return False
    if schema is None: return len(claims)==0
    values=_dict(claims)
    return set(values)==set(schema) and all(type(values[k]) is t for k,t in schema.items())

def validate_fixture_value(value, claims_schema=None):
    if not isinstance(value,JSONObject): return "SCHEMA_TYPE_MISMATCH"
    if _duplicates(value): return "PARSE_DUPLICATE_KEY"
    fields={k for k,_ in value}
    if fields-(TOP_REQUIRED|TOP_OPTIONAL): return "SCHEMA_FIELD_UNKNOWN"
    if not TOP_REQUIRED.issubset(fields): return "SCHEMA_FIELD_MISSING"
    data=_dict(value)
    if type(data["schema_version"]) is not str or data["schema_version"]!=SCHEMA_VERSION:
        return "SCHEMA_VERSION_UNSUPPORTED"
    if type(data["fixture_id"]) is not str or not FIXTURE_RE.fullmatch(data["fixture_id"]):
        return "SCHEMA_SYNTHETIC_ID_INVALID"
    if type(data["case_id"]) is not str or not CASE_RE.fullmatch(data["case_id"]):
        return "SCHEMA_VALUE_OUT_OF_RANGE"
    if type(data["fixture_type"]) is not str or data["fixture_type"] not in D10_TYPES:
        return "SCHEMA_VALUE_OUT_OF_RANGE"
    if type(data["purpose"]) is not str or data["purpose"]!=PURPOSE:
        return "SCHEMA_PURPOSE_UNSUPPORTED"
    subject=data["subject"]
    if not isinstance(subject,JSONObject) or _duplicates(subject): return "SCHEMA_TYPE_MISMATCH"
    subject_fields={k for k,_ in subject}
    if subject_fields!=SUBJECT_FIELDS:
        return "SCHEMA_FIELD_UNKNOWN" if subject_fields-SUBJECT_FIELDS else "SCHEMA_FIELD_MISSING"
    if any(not _synthetic(v) for v in _dict(subject).values()): return "SCHEMA_SYNTHETIC_ID_INVALID"
    if not _claims_valid(data["claims"],claims_schema): return "SCHEMA_TYPE_MISMATCH"
    if "notes" in data and type(data["notes"]) is not str: return "SCHEMA_TYPE_MISMATCH"
    return None

def _reserved(raw):
    return any(b'"'+key.encode("ascii")+b'"' in raw for key in RESERVED)

def validate_oracle_separation(inputs, oracle):
    if not isinstance(inputs,Mapping) or not isinstance(oracle,Mapping) or not inputs or set(inputs)!=set(oracle):
        return False
    for fixture_id, raw in inputs.items():
        if type(fixture_id) is not str or type(raw) is not bytes or _reserved(raw): return False
        record=oracle[fixture_id]
        if not isinstance(record,Mapping) or set(record)!={"expected_reason_code"}: return False
        reason=record["expected_reason_code"]
        if reason is not None and (type(reason) is not str or not reason.startswith(("PARSE_","SCHEMA_"))):
            return False
    return True

def validate_manifest(inputs, oracle, expected_ids, expected_cases, expected_types):
    if not validate_oracle_separation(inputs,oracle): return False
    if len(expected_ids)!=len(set(expected_ids)) or set(inputs)!=set(expected_ids): return False
    if len(expected_types)!=len(D10_TYPES) or set(expected_types)!=D10_TYPES: return False
    required_cases={"SYN-01","SYN-29","SYN-30","SYN-31","SYN-32"}
    if len(expected_cases)!=5 or set(expected_cases)!=required_cases: return False
    observed_cases=set(); observed_types=set()
    for fixture_id,raw in inputs.items():
        parsed=parse_json_bytes(raw)
        if parsed.value is None or parsed.reason_code is not None or validate_fixture_value(parsed.value): return False
        data=_dict(parsed.value)
        if data["fixture_id"]!=fixture_id: return False
        observed_cases.add(data["case_id"]); observed_types.add(data["fixture_type"])
    return observed_cases==required_cases and observed_types==D10_TYPES

def validate_d05_corpus(inputs, oracle, claims_schemas=None):
    if not validate_oracle_separation(inputs,oracle): return False
    schemas=claims_schemas or {}
    for fixture_id,raw in inputs.items():
        parsed=parse_json_bytes(raw); actual=parsed.reason_code
        if parsed.value is not None and actual is None:
            value=_plain(parsed.value); case=value.get("case_id") if isinstance(value,dict) else None
            actual=validate_fixture_value(parsed.value,schemas.get(case))
        if actual!=oracle[fixture_id]["expected_reason_code"]: return False
    return True

def measure_json_value(value):
    result={"max_depth":0,"max_object_members":0,"max_array_items":0,
            "max_string_value_bytes":0,"max_string_key_bytes":0,"scalar_nodes":0}
    def visit(node,depth):
        if isinstance(node,JSONObject):
            d=depth+1; result["max_depth"]=max(result["max_depth"],d)
            result["max_object_members"]=max(result["max_object_members"],len(node))
            for key,child in node:
                result["max_string_key_bytes"]=max(result["max_string_key_bytes"],len(key.encode("utf-8")))
                visit(child,d)
        elif isinstance(node,list):
            d=depth+1; result["max_depth"]=max(result["max_depth"],d)
            result["max_array_items"]=max(result["max_array_items"],len(node))
            for child in node: visit(child,d)
        elif isinstance(node,str):
            result["scalar_nodes"]+=1
            result["max_string_value_bytes"]=max(result["max_string_value_bytes"],len(node.encode("utf-8")))
        elif node is None or type(node) in (bool,int,float): result["scalar_nodes"]+=1
    visit(value,0); return result

def measure_parser_input(raw: bytes):
    if type(raw) is not bytes: raise TypeError("parser input must be bytes")
    parsed=parse_json_bytes(raw)
    result={"raw_bytes":len(raw),"max_depth":None,"max_object_members":None,
        "max_array_items":None,"max_string_value_bytes":None,"max_string_key_bytes":None,
        "scalar_nodes":None,"not_applicable_reason":None,"parse_reason_code":parsed.reason_code,
        "duplicate_key_count":len(parsed.duplicate_paths)}
    if parsed.value is None: result["not_applicable_reason"]=parsed.reason_code
    else:
        result.update(measure_json_value(parsed.value))
        if parsed.reason_code: result["not_applicable_reason"]=parsed.reason_code
    return result

def corpus_digest(inputs, ordered_ids):
    if set(inputs)!=set(ordered_ids) or len(ordered_ids)!=len(set(ordered_ids)):
        raise ValueError("manifest/input ID mismatch")
    digest=hashlib.sha256()
    for fixture_id in ordered_ids:
        raw=inputs[fixture_id]
        if type(raw) is not bytes: raise TypeError("parser input must be bytes")
        digest.update(len(raw).to_bytes(8,"big")); digest.update(raw)
    return digest.hexdigest()

def measure_corpus(inputs, ordered_ids):
    rows=[{"fixture_id":fid,**measure_parser_input(inputs[fid])} for fid in ordered_ids]
    aggregates=recompute_aggregates(rows)
    return {"rows":rows,"aggregates":aggregates,"corpus_sha256":corpus_digest(inputs,ordered_ids)}

def recompute_aggregates(rows):
    dims=("max_depth","max_object_members","max_array_items","max_string_value_bytes","max_string_key_bytes","scalar_nodes")
    result={"fixture_count":len(rows),"total_raw_bytes":sum(row["raw_bytes"] for row in rows)}
    for dim in dims:
        values=[row[dim] for row in rows if row.get(dim) is not None]
        result[dim]=max(values) if values else None
    return result

def validate_provenance(provenance, source_bytes, frozen_sha):
    required={"corpus_revision","source_commit","source_blob_sha256","command","python_version","platform","measurement_definition_revision"}
    if not isinstance(provenance,Mapping) or set(provenance)!=required or type(source_bytes) is not bytes: return False
    if type(frozen_sha) is not str or not SHA_RE.fullmatch(frozen_sha): return False
    if hashlib.sha256(source_bytes).hexdigest()!=frozen_sha: return False
    if not SHA_RE.fullmatch(str(provenance["source_blob_sha256"])): return False
    if not re.fullmatch(r"[0-9a-f]{40,64}",str(provenance["source_commit"])): return False
    return all(type(provenance[k]) is str and bool(provenance[k].strip()) for k in required)

def runtime_provenance(corpus_revision, source_commit, source_blob_sha256, command):
    return {"corpus_revision":corpus_revision,"source_commit":source_commit,
        "source_blob_sha256":source_blob_sha256,"command":command,"python_version":sys.version,
        "platform":platform.platform(),"measurement_definition_revision":MEASUREMENT_DEFINITION_REVISION}

def validate_capability_boundary(source_bytes,boundary):
    if type(source_bytes) is not bytes or boundary not in {"persistence","external"}: return False
    try: tree=ast.parse(source_bytes.decode("utf-8"))
    except (UnicodeDecodeError,SyntaxError): return False
    forbidden={"os","pathlib","tempfile","shutil","socket","requests","urllib","http","sqlite3",
        "psycopg","ccxt","subprocess","ftplib","paramiko","boto3","importlib","ctypes","runpy",
        "builtins","urllib3","httpx","aiohttp","websocket","websockets","redis","pymongo",
        "sqlalchemy","psycopg2","mysql","asyncpg","aiosqlite","google","azure"}
    builtin_calls={"open","exec","eval","compile","__import__"}
    writes={"write_text","write_bytes","unlink","remove","rmtree","mkdir","makedirs","mkstemp",
        "NamedTemporaryFile","TemporaryDirectory"}
    for node in ast.walk(tree):
        if isinstance(node,ast.Import) and {a.name.split(".")[0] for a in node.names}&forbidden: return False
        if isinstance(node,ast.ImportFrom) and (node.module or "").split(".")[0] in forbidden: return False
        if isinstance(node,ast.Call):
            if isinstance(node.func,ast.Name) and node.func.id in builtin_calls: return False
            attr=node.func.attr if isinstance(node.func,ast.Attribute) else ""
            if attr in {"import_module","exec_module","open"}: return False
            if boundary=="persistence" and attr in writes: return False
    return True

def validate_execution_trace(trace):
    keys={"payload_persistence_events","external_access_events"}
    return isinstance(trace,Mapping) and set(trace)==keys and all(
        isinstance(trace[k],(list,tuple)) and len(trace[k])==0 for k in keys)

def build_report(corpus_revision,measurement,assertions,provenance):
    if not isinstance(measurement,Mapping) or set(measurement)!={"rows","aggregates","corpus_sha256"}:
        raise ValueError("invalid measurement shape")
    ids={f"A-{i:02d}" for i in range(1,14)}
    if not isinstance(assertions,Mapping) or set(assertions)!=ids or any(type(v) is not bool for v in assertions.values()):
        raise ValueError("all A-01..A-13 boolean assertions are required")
    report={"report_schema":"S1-MEASUREMENT-REPORT-V1","corpus_revision":corpus_revision,
        "measurement":dict(measurement),"assertions":dict(assertions),"provenance":dict(provenance)}
    return json.dumps(report,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")

def validate_report_readback(report_bytes):
    if type(report_bytes) is not bytes: return False
    parsed=parse_json_bytes(report_bytes)
    if parsed.value is None or parsed.reason_code is not None: return False
    report=_plain(parsed.value)
    if not isinstance(report,dict) or set(report)!={"report_schema","corpus_revision","measurement","assertions","provenance"}: return False
    if report["report_schema"]!="S1-MEASUREMENT-REPORT-V1": return False
    m=report["measurement"]
    if not isinstance(m,dict) or set(m)!={"rows","aggregates","corpus_sha256"} or not isinstance(m["rows"],list): return False
    if recompute_aggregates(m["rows"])!=m["aggregates"]: return False
    ids={f"A-{i:02d}" for i in range(1,14)}
    return isinstance(report["assertions"],dict) and set(report["assertions"])==ids and all(
        type(v) is bool for v in report["assertions"].values()) and isinstance(report["provenance"],dict)

def evaluate_assertions(e):
    checks={
      "A-01":lambda:validate_manifest(e["parser_inputs"],e["oracle_records"],e["expected_fixture_ids"],e["expected_case_ids"],e["expected_fixture_types"]),
      "A-02":lambda:validate_d05_corpus(e["parser_inputs"],e["oracle_records"],e.get("claims_schemas")),
      "A-03":lambda:bool(e["parser_inputs"]) and all(not _reserved(raw) for raw in e["parser_inputs"].values()),
      "A-04":lambda:bool(e["parser_inputs"]) and validate_oracle_separation(e["parser_inputs"],e["oracle_records"]),
      "A-05":lambda:bool(e["parser_inputs"]) and all(measure_parser_input(raw)["raw_bytes"]==len(raw) for raw in e["parser_inputs"].values()),
      "A-06":lambda:bool(e["parser_inputs"]) and all(parse_json_bytes(raw).reason_code==(e["oracle_records"][fid]["expected_reason_code"] if str(e["oracle_records"][fid]["expected_reason_code"] or "").startswith("PARSE_") else None) for fid,raw in e["parser_inputs"].items()),
      "A-07":lambda:bool(e["parser_inputs"]) and all(set(measure_parser_input(raw))=={"raw_bytes","max_depth","max_object_members","max_array_items","max_string_value_bytes","max_string_key_bytes","scalar_nodes","not_applicable_reason","parse_reason_code","duplicate_key_count"} and (measure_parser_input(raw)["not_applicable_reason"] is None or bool(measure_parser_input(raw)["not_applicable_reason"])) for raw in e["parser_inputs"].values()),
      "A-08":lambda:recompute_aggregates(e["measurement"]["rows"])==e["measurement"]["aggregates"],
      "A-09":lambda:e["measurement_pass_1"]==e["measurement_pass_2"],
      "A-10":lambda:validate_provenance(e["provenance"],e["harness_source_bytes"],e["frozen_source_sha256"]),
      "A-11":lambda:validate_report_readback(e["report_bytes"]),
      "A-12":lambda:validate_execution_trace({"payload_persistence_events":e["execution_trace"]["payload_persistence_events"],"external_access_events":[]}) and validate_capability_boundary(e["harness_source_bytes"],"persistence"),
      "A-13":lambda:validate_execution_trace({"payload_persistence_events":[],"external_access_events":e["execution_trace"]["external_access_events"]}) and validate_capability_boundary(e["harness_source_bytes"],"external"),
    }
    results={}
    for key,check in checks.items():
        try: results[key]=check() is True
        except (KeyError,TypeError,ValueError,AttributeError): results[key]=False
    return results
