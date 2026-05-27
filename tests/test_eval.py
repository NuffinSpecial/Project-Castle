from asl_translator.eval import run_eval


def test_eval_set_runs(pipeline):
    report = run_eval(pipeline)
    assert report.total >= 5
    assert report.token_accuracy >= 0.7
