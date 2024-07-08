from hypothesis import strategies as st
from hypothesis import given


#define reverse function
def reverse(ls) -> list:
     return ls[::-1]

#make test data -- 
#@given(st.lists([st.integers(min_value=1, max_value=1000), 
#                st.floats(min_value = 0.1, max_value=1000),
#               st.from_regex(r"^[a-zA-Z0-9]{1,4}$")]))

@given(st.lists(st.integers(min_value=1, max_value=100)))
def test_reverse(l):
    #generate reversed list
    r = reverse(l)
    assert len(r) == len(l)
    assert set(r) == set(r)
    assert r[::-1] == l
    
                