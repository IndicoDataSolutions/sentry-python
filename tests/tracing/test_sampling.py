from sentry_sdk import start_span, start_transaction


def test_sampling_decided_only_for_transactions(sentry_init, capture_events):
    sentry_init(traces_sample_rate=0.5)

    with start_transaction(name="hi") as transaction:
        assert transaction.sampled is not None

        with start_span() as span:
            assert span.sampled == transaction.sampled

    with start_span() as span:
        assert span.sampled is None


def test_nested_transaction_sampling_override():
    with start_transaction(name="outer", sampled=True) as outer_transaction:
        assert outer_transaction.sampled is True
        with start_transaction(name="inner", sampled=False) as inner_transaction:
            assert inner_transaction.sampled is False
        assert outer_transaction.sampled is True


def test_no_double_sampling(sentry_init, capture_events):
    # Transactions should not be subject to the global/error sample rate.
    # Only the traces_sample_rate should apply.
    sentry_init(traces_sample_rate=1.0, sample_rate=0.0)
    events = capture_events()

    with start_transaction(name="/"):
        pass

    assert len(events) == 1


@pytest.mark.parametrize("sampling_decision", [True, False])
def test_get_transaction_and_span_from_scope_regardless_of_sampling_decision(
    sentry_init, sampling_decision
):
    sentry_init(traces_sample_rate=1.0)

    with start_transaction(name="/", sampled=sampling_decision):
        with start_span(op="child-span"):
            with start_span(op="child-child-span"):
                scope = Hub.current.scope
                assert scope.span.op == "child-child-span"
                assert scope.transaction.name == "/"
