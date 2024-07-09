from hypothesis import strategies as st
from hypothesis import given
from hypothesis.stateful import rule, precondition, RuleBasedStateMachine, Bundle



# define reverse function
def reverse(ls) -> list:
     return ls[::-1]

# make test data 
# test list can have elements that are int, float or str
@given(st.lists(
    st.one_of(
    [st.integers(min_value=1, max_value=1000), 
     st.floats(min_value = 0.1, max_value=1000),
     st.from_regex(r"^[a-zA-Z0-9]{1,4}$")]
    ),
     min_size=10, max_size=20))
      
def test_reverse(l):
    # generate reversed list
    r = reverse(l)
    # test reverse list
    assert len(r) == len(l)
    assert set(r) == set(r)
    assert r[::-1] == l
    

#@given(st.one_of(st.lists(st.integers(min_value=1, max_value=100)),
#       st.lists(st.from_regex(r"^[a-zA-Z0-9]{1,4}$"))))



