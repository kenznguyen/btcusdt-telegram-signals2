import copy, hashlib, inspect, json, unittest
from tools.s1_measurement_harness import (
 D10_TYPES, SCHEMA_VERSION, PURPOSE, build_report, corpus_digest, evaluate_assertions,
 measure_corpus, measure_parser_input, parse_json_bytes, recompute_aggregates,
 runtime_provenance, validate_capability_boundary, validate_d05_corpus,
 validate_fixture_value, validate_manifest, validate_oracle_separation,
 validate_provenance, validate_report_readback,
)

def fixture_bytes(fid,case,kind,claims=None):
 value={"schema_version":SCHEMA_VERSION,"fixture_id":fid,"case_id":case,"fixture_type":kind,
  "subject":{"object_id":"syn-object-001","version_id":"syn-version-001","namespace":"syn-namespace-001"},
  "purpose":PURPOSE,"claims":{} if claims is None else claims}
 return json.dumps(value,separators=(",",":"),ensure_ascii=True).encode()

def valid_corpus():
 kinds=sorted(D10_TYPES); cases=["SYN-01","SYN-29","SYN-30","SYN-31","SYN-32"]
 inputs={f"syn-fixture-{i:03d}":fixture_bytes(f"syn-fixture-{i:03d}",cases[i%5],kind) for i,kind in enumerate(kinds,1)}
 oracle={fid:{"expected_reason_code":None} for fid in inputs}
 manifest={fid:{"case_id":cases[i%5],"fixture_type":kind} for i,(fid,kind) in enumerate(zip(inputs,kinds))}
 return inputs,oracle,manifest,list(inputs),cases,kinds

class MeasurementHarnessTests(unittest.TestCase):
 def test_valid_synthetic_fixture_conforms_to_d05_and_d10(self):
  raw=fixture_bytes("syn-fixture-001","SYN-01",sorted(D10_TYPES)[0])
  parsed=parse_json_bytes(raw); self.assertIsNone(parsed.reason_code); self.assertIsNone(validate_fixture_value(parsed.value))
 def test_rejects_unknown_and_missing_top_level_fields(self):
  import tools.s1_measurement_harness as h
  value=h._plain(parse_json_bytes(fixture_bytes("syn-fixture-001","SYN-01",sorted(D10_TYPES)[0])).value)
  value["unexpected"]="x"; self.assertEqual(validate_fixture_value(h._pairs(list(value.items()))),"SCHEMA_FIELD_UNKNOWN")
  value.pop("unexpected"); value.pop("purpose")
  self.assertEqual(validate_fixture_value(h._pairs(list(value.items()))),"SCHEMA_FIELD_MISSING")
 def test_rejects_wrong_exact_types_and_non_synthetic_identifiers(self):
  import tools.s1_measurement_harness as h
  value=h._plain(parse_json_bytes(fixture_bytes("syn-fixture-001","SYN-01",sorted(D10_TYPES)[0])).value)
  value["fixture_id"]="production-1"
  self.assertEqual(validate_fixture_value(h._pairs(list(value.items()))),"SCHEMA_SYNTHETIC_ID_INVALID")
  value["fixture_id"]="syn-fixture-001"; value["subject"]["object_id"]="real-object"
  pairs=[(k,h._pairs(list(v.items())) if k=="subject" else v) for k,v in value.items()]
  self.assertEqual(validate_fixture_value(h._pairs(pairs)),"SCHEMA_SYNTHETIC_ID_INVALID")
 def test_case_specific_claim_schema_is_closed_and_exact_typed(self):
  parsed=parse_json_bytes(fixture_bytes("syn-fixture-001","SYN-01",sorted(D10_TYPES)[0],{"count":3}))
  self.assertIsNone(validate_fixture_value(parsed.value,{"count":int}))
  self.assertEqual(validate_fixture_value(parsed.value,{"count":bool}),"SCHEMA_TYPE_MISMATCH")
  self.assertEqual(validate_fixture_value(parsed.value,{"count":int,"extra":str}),"SCHEMA_TYPE_MISMATCH")
 def test_duplicate_keys_detected_at_top_and_nested_levels(self):
  self.assertEqual(parse_json_bytes(b'{"a":1,"a":2}').reason_code,"PARSE_DUPLICATE_KEY")
  nested=parse_json_bytes(b'{"outer":{"x":1,"x":2}}')
  self.assertEqual(nested.reason_code,"PARSE_DUPLICATE_KEY"); self.assertEqual(len(nested.duplicate_paths),1)
 def test_rejects_invalid_utf8_malformed_nonfinite_and_trailing_json(self):
  self.assertEqual(parse_json_bytes(b"\xff").reason_code,"PARSE_INVALID_UTF8")
  self.assertEqual(parse_json_bytes(b'{"x":').reason_code,"PARSE_INVALID_JSON")
  self.assertEqual(parse_json_bytes(b'{"x":NaN}').reason_code,"PARSE_NONFINITE_NUMBER")
  self.assertEqual(parse_json_bytes(b'{"x":1e999}').reason_code,"PARSE_NONFINITE_NUMBER")
  self.assertEqual(parse_json_bytes(b'{}{}').reason_code,"PARSE_INVALID_JSON")
 def test_rejects_invalid_unicode_scalar(self):
  self.assertEqual(parse_json_bytes(b'"\\ud800"').reason_code,"PARSE_INVALID_UNICODE")
 def test_oracle_separation_and_exact_key_correspondence(self):
  inputs,oracle,manifest,ids,cases,kinds=valid_corpus()
  self.assertTrue(validate_oracle_separation(inputs,oracle))
  self.assertFalse(validate_oracle_separation(inputs,{**oracle,"syn-fixture-extra":{"expected_reason_code":None}}))
  injected=dict(inputs); injected[ids[0]]=injected[ids[0]].replace(b'"claims":{}',b'"claims":{},"expected":{}')
  self.assertFalse(validate_oracle_separation(injected,oracle))
 def test_manifest_requires_exact_inventory_five_cases_and_all_d10(self):
  inputs,oracle,manifest,ids,cases,kinds=valid_corpus()
  self.assertTrue(validate_manifest(inputs,oracle,manifest,ids,cases,kinds))
  self.assertFalse(validate_manifest(inputs,oracle,manifest,ids[:-1],cases,kinds))
  self.assertFalse(validate_manifest(inputs,oracle,manifest,ids,cases,kinds[:-1]))
  malformed=dict(inputs); malformed[ids[0]]=b"\\xff"
  self.assertTrue(validate_manifest(malformed,oracle,manifest,ids,cases,kinds))
  bad_manifest=dict(manifest); bad_manifest["production-id"]=bad_manifest.pop(ids[0])
  bad_inputs=dict(malformed); bad_inputs["production-id"]=bad_inputs.pop(ids[0])
  bad_oracle=dict(oracle); bad_oracle["production-id"]=bad_oracle.pop(ids[0])
  self.assertFalse(validate_manifest(bad_inputs,bad_oracle,bad_manifest,list(bad_inputs),cases,kinds))
  malformed=dict(inputs); malformed[ids[0]]=b"\\xff"
  self.assertTrue(validate_manifest(malformed,oracle,manifest,ids,cases,kinds))
 def test_d05_accepts_declared_parse_negative_and_positive_controls(self):
  inputs,oracle,manifest,ids,cases,kinds=valid_corpus(); self.assertTrue(validate_d05_corpus(inputs,oracle))
  fid=ids[0]; inputs[fid]=b'{"x":1,"x":2}'; oracle[fid]={"expected_reason_code":"PARSE_DUPLICATE_KEY"}
  self.assertTrue(validate_d05_corpus(inputs,oracle))
 def test_d05_rejects_oracle_mismatch(self):
  inputs,oracle,manifest,ids,cases,kinds=valid_corpus(); oracle[ids[0]]={"expected_reason_code":"SCHEMA_FIELD_MISSING"}
  self.assertFalse(validate_d05_corpus(inputs,oracle))
 def test_measurement_uses_exact_bytes_and_root_depth_one(self):
  raw=b'{"a":[{"b":"\xc3\xa9"}]}'; m=measure_parser_input(raw)
  self.assertEqual(m["raw_bytes"],len(raw)); self.assertEqual(m["max_depth"],3)
  self.assertEqual(m["max_string_value_bytes"],2); self.assertEqual(m["max_string_key_bytes"],1)
  self.assertEqual(m["scalar_nodes"],1)
 def test_malformed_input_reports_raw_bytes_and_reasoned_na(self):
  m=measure_parser_input(b"\xff"); self.assertEqual(m["raw_bytes"],1)
  self.assertIsNone(m["max_depth"]); self.assertEqual(m["not_applicable_reason"],"PARSE_INVALID_UTF8")
 def test_duplicate_payload_is_pair_preserved_for_structural_measurement(self):
  m=measure_parser_input(b'{"x":1,"x":2}')
  self.assertEqual(m["max_object_members"],2); self.assertEqual(m["duplicate_key_count"],1)
 def test_digest_is_ordered_and_length_prefixed(self):
  inputs={"syn-fixture-a":b"ab","syn-fixture-b":b"c"}
  expected=hashlib.sha256((2).to_bytes(8,"big")+b"ab"+(1).to_bytes(8,"big")+b"c").hexdigest()
  self.assertEqual(corpus_digest(inputs,list(inputs)),expected)
  self.assertNotEqual(corpus_digest(inputs,list(inputs)),corpus_digest(inputs,list(reversed(inputs))))
 def test_aggregate_recomputed_from_rows(self):
  inputs,oracle,manifest,ids,cases,kinds=valid_corpus(); m=measure_corpus(inputs,ids)
  self.assertEqual(recompute_aggregates(m["rows"]),m["aggregates"])
 def test_provenance_hash_is_computed_and_compared(self):
  source=b"frozen harness source"; digest=hashlib.sha256(source).hexdigest()
  provenance=runtime_provenance("corpus-v1","a"*40,hashlib.sha256(source).hexdigest(),"python -m unittest")
  self.assertTrue(validate_provenance(provenance,source,digest))
  self.assertFalse(validate_provenance(provenance,source+b"tampered",digest))
 def test_report_readback_checks_schema_aggregate_and_duplicate_keys(self):
  inputs,oracle,manifest,ids,cases,kinds=valid_corpus(); m=measure_corpus(inputs,ids)
  assertions={f"A-{i:02d}":True for i in range(1,14)}
  provenance=runtime_provenance("corpus-v1","a"*40,"b"*64,"measure")
  report=build_report("corpus-v1",m,assertions,provenance); self.assertTrue(validate_report_readback(report))
  broken=json.loads(report); broken["measurement"]["aggregates"]["total_raw_bytes"]+=1
  self.assertFalse(validate_report_readback(json.dumps(broken).encode()))
  duplicate=report.replace(b'"report_schema":',b'"report_schema":"S1-MEASUREMENT-REPORT-V1","report_schema":',1)
  self.assertFalse(validate_report_readback(duplicate))
  unsafe=json.loads(report); unsafe["measurement"]["rows"][0]["raw_payload"]="must-not-be-reported"
  self.assertFalse(validate_report_readback(json.dumps(unsafe).encode()))
 def test_assertion_registry_has_thirteen_executable_checks_and_missing_fails_closed(self):
  results=evaluate_assertions({})
  self.assertEqual(set(results),{f"A-{i:02d}" for i in range(1,14)})
  self.assertFalse(any(results.values()))
 def test_static_capability_boundary_rejects_file_and_network_io(self):
  safe=b"def pure(value):\n    return value + 1\n"
  file_code=b"def bad(path):\n    with open(path, 'wb') as handle: handle.write(b'x')\n"
  network=b"import socket\ndef bad(): return socket.socket()\n"
  self.assertTrue(validate_capability_boundary(safe,"persistence"))
  self.assertTrue(validate_capability_boundary(safe,"external"))
  self.assertFalse(validate_capability_boundary(file_code,"persistence"))
  self.assertFalse(validate_capability_boundary(network,"external"))
 def test_measurement_api_rejects_combined_oracle_object(self):
  with self.assertRaises(TypeError): measure_parser_input({"raw":b"x","expected":{"reason":"x"}})
 def test_all_thirteen_assertions_pass_on_complete_evidence(self):
  inputs,oracle,manifest,ids,cases,kinds=valid_corpus(); m=measure_corpus(inputs,ids)
  source=inspect.getsource(__import__("tools.s1_measurement_harness",fromlist=["x"])).encode()
  provenance=runtime_provenance("corpus-v1","a"*40,hashlib.sha256(source).hexdigest(),"python -m unittest")
  report=build_report("corpus-v1",m,{f"A-{i:02d}":True for i in range(1,14)},provenance)
  e={"parser_inputs":inputs,"oracle_records":oracle,"manifest":manifest,"expected_fixture_ids":ids,"expected_case_ids":cases,
   "expected_fixture_types":kinds,"measurement":m,"measurement_pass_1":m,"measurement_pass_2":m,
   "provenance":provenance,"harness_source_bytes":source,"frozen_source_sha256":hashlib.sha256(source).hexdigest(),
   "report_bytes":report,"execution_trace":{"payload_persistence_events":[],"external_access_events":[]}}
  self.assertEqual(evaluate_assertions(e),{f"A-{i:02d}":True for i in range(1,14)})
 def test_each_assertion_fails_closed_when_its_evidence_is_broken(self):
  inputs,oracle,manifest,ids,cases,kinds=valid_corpus(); m=measure_corpus(inputs,ids)
  source=inspect.getsource(__import__("tools.s1_measurement_harness",fromlist=["x"])).encode()
  provenance=runtime_provenance("corpus-v1","a"*40,hashlib.sha256(source).hexdigest(),"python -m unittest")
  report=build_report("corpus-v1",m,{f"A-{i:02d}":True for i in range(1,14)},provenance)
  base={"parser_inputs":inputs,"oracle_records":oracle,"manifest":manifest,"expected_fixture_ids":ids,"expected_case_ids":cases,
   "expected_fixture_types":kinds,"measurement":m,"measurement_pass_1":m,"measurement_pass_2":m,
   "provenance":provenance,"harness_source_bytes":source,"frozen_source_sha256":hashlib.sha256(source).hexdigest(),
   "report_bytes":report,"execution_trace":{"payload_persistence_events":[],"external_access_events":[]}}
  mutations={
   "A-01":lambda e:e.update(expected_fixture_ids=ids[:-1]),
   "A-02":lambda e:e["oracle_records"].update({ids[0]:{"expected_reason_code":"SCHEMA_FIELD_MISSING"}}),
   "A-03":lambda e:e["parser_inputs"].update({ids[0]:inputs[ids[0]].replace(b'"claims":{}',b'"claims":{},"expected":{}')}),
   "A-04":lambda e:e["oracle_records"].pop(ids[0]),
   "A-05":lambda e:e["parser_inputs"].update({ids[0]:"not-bytes"}),
   "A-06":lambda e:e["oracle_records"].update({ids[0]:{"expected_reason_code":"PARSE_DUPLICATE_KEY"}}),
   "A-07":lambda e:e["parser_inputs"].update({ids[0]:"not-bytes"}),
   "A-08":lambda e:e["measurement"]["aggregates"].update(total_raw_bytes=-1),
   "A-09":lambda e:e.update(measurement_pass_2={"different":True}),
   "A-10":lambda e:e.update(frozen_source_sha256="0"*64),
   "A-11":lambda e:e.update(report_bytes=b"not-json"),
   "A-12":lambda e:e["execution_trace"].update(payload_persistence_events=["write"]),
   "A-13":lambda e:e["execution_trace"].update(external_access_events=["network"]),
  }
  for assertion,mutate in mutations.items():
   with self.subTest(assertion=assertion):
    evidence=copy.deepcopy(base); mutate(evidence)
    self.assertIs(evaluate_assertions(evidence)[assertion],False)

if __name__=="__main__": unittest.main()
