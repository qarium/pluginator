import hamcrest as h

TEST_CONST = 'global'


def test_call_context(test_func):
    result = test_func()

    h.assert_that(result, h.has_entry('__name__', 'tests.test_utils'))
    h.assert_that(result, h.has_entry('__package__', 'tests'))
    h.assert_that(result, h.has_entry('TEST_CONST', h.equal_to(TEST_CONST)))
    h.assert_that(result, h.is_not(h.has_item('local_var')))
