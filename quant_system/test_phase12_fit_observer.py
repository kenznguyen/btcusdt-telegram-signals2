"""Phase 12 observation cannot invalidate a fitted paper-only FreqAI booster."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from quant_system.phase12_fit_observer import observe_post_fit, read_observer_errors


class FitObserverTests(TestCase):
    def test_failed_evidence_observer_returns_fitted_model_and_records_failure(self):
        with TemporaryDirectory() as tmp:
            output=Path(tmp)/'observer-errors.jsonl'
            model=object()
            def broken():
                raise ValueError('PHASE12_FIT_INDEX_IDENTITY_UNVERIFIED')
            actual=observe_post_fit(model,broken,output,'fold-1')
            self.assertIs(actual,model)
            errors=read_observer_errors(output)
            self.assertEqual(len(errors),1)
            self.assertEqual(errors[0]['error_code'],
                             'PHASE12_FIT_INDEX_IDENTITY_UNVERIFIED')
            self.assertEqual(errors[0]['fold_model_name'],'fold-1')

    def test_successful_observer_keeps_model_and_no_errors(self):
        with TemporaryDirectory() as tmp:
            output=Path(tmp)/'observer-errors.jsonl'
            model=object()
            visited=[]
            actual=observe_post_fit(model,lambda:visited.append(True),output,'fold-1')
            self.assertIs(actual,model)
            self.assertEqual(visited,[True])
            self.assertFalse(output.exists())
            self.assertEqual(read_observer_errors(output),[])

    def test_multiple_observation_failures_are_not_overwritten(self):
        with TemporaryDirectory() as tmp:
            output=Path(tmp)/'observer-errors.jsonl'
            for i in (1,2):
                def fail():
                    raise RuntimeError('FIT_DATA_UNAVAILABLE')
                observe_post_fit(object(),fail,output,f'fold-{i}')
            self.assertEqual([e['fold_model_name'] for e in read_observer_errors(output)],
                             ['fold-1','fold-2'])

    def test_missing_or_tampered_diagnostic_record_is_rejected(self):
        with TemporaryDirectory() as tmp:
            output=Path(tmp)/'observer-errors.jsonl'
            output.write_text('this is not json\n')
            with self.assertRaises(ValueError):
                read_observer_errors(output)

    def test_does_not_swallow_process_interrupt(self):
        with TemporaryDirectory() as tmp:
            output=Path(tmp)/'observer-errors.jsonl'
            def stop():
                raise KeyboardInterrupt()
            with self.assertRaises(KeyboardInterrupt):
                observe_post_fit(object(),stop,output,'fold-1')
