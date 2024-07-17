from hypothesis import strategies as st
from hypothesis import given
from hypothesis.extra.numpy import arrays
from hypothesis import settings, HealthCheck
from hypothesis.strategies import composite

import xarray as xr
import numpy as np
from custom_index import create_sample_data, make_kwargs, ToyIndex_scalar

# this script creates test data that will be used when testing the xr custom index transform operations
#inputs to strategy fns 
range_kwargs = {'start':[0,1000], #start can be any value, must be less than stop
                'stop':[1,1000], # stop needs to be at least 1
                'step':[1,10], #step must be less than stop
                'data_len':100,
                'range':slice(0,200,2)
               }

@composite #this means that return is not expected to be value, not strategy 
def create_ds_strategy(draw, **kwargs):
    '''fn to create ds obect to be used in testing
    '''

    #for now, hardcode this just to get a range we know will work
    range_slice = kwargs['range']
    data_len = kwargs['data_len']
    
    #first, create attrs (store metadata for transform)
    attrs_dict_st = st.fixed_dictionaries({
        'factor': st.one_of(st.integers(min_value=1, max_value=1000),
                            st.floats(min_value=0.1, max_value=1000)),
        'range' : st.just(range_slice),
        'idx_name' : st.just("x"),
        'real_name': st.just("lon"),
        })  
    
    #leave strategy world with draw()
    attrs_dict = draw(attrs_dict_st)
    
    # this is a normal xr.DA not a strategy bc attr is a dict not strategy
    scalar_da = xr.DataArray(0)
    
    #make dims 
    dims = ['x','y']
    #make params for x coord - not in strategy world
    start = range_slice.start
    stop = range_slice.stop
    step = range_slice.step
              
    #make coord dict strategy
    #to do this, generate a strategy for y
    y_st = arrays(shape = 1,
                  dtype=np.float64)
    # then leave strategy world
    y = draw(y_st)
    # to create an explicit coord
    coords = {'x':np.arange(start, stop, step), 
              'y':y}

    #make data strategy (Want some randomness)
    data_vars_st = arrays(dtype=np.float64, shape=(data_len,1), elements=st.floats(min_value=1, max_value=100))
    #leave strategy world, make explicit variable array
    data_vars = draw(data_vars_st)
    
    #make xr.Da (Explicit)
    da = xr.DataArray(data = data_vars,
                      coords=coords,
                      dims=dims)
    #make xr.DS (Explicit)
    ds = xr.Dataset(data_vars = {
                                'spatial_ref': scalar_da,
                                'var1':da})
    ds['spatial_ref'].attrs = attrs_dict
    #return xr.DS
    # callign this function will still return a strategy object, still need to call example
    # but composite is doing magic of going from explicit obj to strategy (<- i think)
    return ds    


#now tests
@given(create_ds_strategy(**range_kwargs))
def test_ds(ds):
    
    assert list(ds['spatial_ref'].attrs.keys()) == ['factor', 'range', 'idx_name', 'real_name']
    assert ds['spatial_ref'].attrs['range'].start == np.min(ds.x.data)
    # y dim being len 1 is hardcoded here
    assert ds.var1.data.shape == (int(range_kwargs['data_len']),1)
    
       