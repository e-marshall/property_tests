from hypothesis import strategies as st
from hypothesis import given
from hypothesis.extra.numpy import arrays
import xarray as xr
import numpy as np

# this script creates test data that will be used when testing the xr custom index transform operations
# for now the datas not realistic 

#helper fns
def make_range_ls():
    '''i'm a function to create the range that is an attr of the dataset
    '''
    start = st.integers(min_value=0, max_value = 10000)
    stop = st.integers(min_value=0, max_value = 10000)
    step = st.integers(min_value=0, max_value = 10000)
    rn = st.tuples(start, stop, step).filter(lambda x: x[0] < x[1] ).map(list)
    return rn
    

#should this be a class ?
# pass attr key names (these will change): ['factor','range','idx_name','real_name']
# pass min, max values for factor, x coord, y coord, data
def create_ds_strategy():
    '''fn to create ds obect to be used in testing
    '''

    #first, create attrs (store metadata for transform)
    attrs_dict_st = st.fixed_dictionaries({
        'factor': st.one_of(st.integers(min_value=1, max_value=1000),
                            st.floats(min_value=0.1, max_value=1000)),
        'range' : make_range_ls(),
        'idx_name' : st.from_regex(r"^x$"),
        'real_name': st.from_regex(r"^lon$"),
        })  

    scalar_da = st.builds(xr.DataArray, attrs=attrs_dict_st)
    #make dims
    dims = st.just(['x','y'])

    #make coords- hardcoded some bounds in here 
    #for coords (for now), want y=1, x is longer, but must be monotonically increasing, no duplicates
    coords = st.fixed_dictionaries({
            'x': st.sets(st.integers(min_value=-100, max_value=100), min_size=100, max_size=100).map(lambda x: np.array(sorted(x))),
            'y': arrays(dtype=np.float64, shape=1, elements = st.floats(min_value=-10, max_value=100))
                })
    
    #make data, hardcoded shape, name
    data_vars = values = arrays(dtype=np.float64, shape=(100,1), elements=st.floats(min_value=1, max_value=100))

    #make xr object
    da_st = st.builds(xr.DataArray, data = data_vars,
                  coords=coords,
                  dims=dims
                 )
    ds_st = st.builds(xr.Dataset, 
                      data_vars = st.fixed_dictionaries({
                          'spatial_ref': scalar_da,
                          'var1':da_st})
                     )
    return ds_st

#now tests
@given(create_ds_strategy())
def test_ds(ds):
    assert list(ds.spatial_ref.attrs.keys()) == ['factor', 'range', 'idx_name', 'real_name']
    assert ds.var1.data.shape == (100,1)
    
       