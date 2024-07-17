import xarray as xr 
import numpy as np
import pandas as pd
from collections.abc import Sequence
from copy import deepcopy


from xarray import Index
from xarray.core.indexes import PandasIndex
from xarray.core.indexing import merge_sel_results
import matplotlib.pyplot as plt
from xarray.core.indexes import Index, PandasIndex, get_indexer_nd
from xarray.core.indexing import merge_sel_results

def create_sample_data(kwargs):
    attrs = {
    'factor' : kwargs['factor'],
    'range' : kwargs['range'],
    'idx_name' : kwargs['idx_name'],
    'real_name' : kwargs['real_name'] 
    }
    da = xr.DataArray(
        data = np.random.rand(kwargs['data_len']),
        dims = (kwargs['idx_name']),
        coords = {
            'x':np.arange(kwargs['range'][0], kwargs['range'][1],kwargs['range'][2]),
            })
    ds = xr.Dataset({'var1':da
                    })
    spatial_ref = xr.DataArray()
    spatial_ref.attrs = attrs

    ds['spatial_ref'] = spatial_ref
    ds = ds.set_coords('spatial_ref')

    ds = ds.expand_dims({'y':1})
    return ds

def make_kwargs(factor, range_ls, data_len):
    da_kwargs = {
        'factor': factor,
        'range' : range_ls,
        'idx_name':'x',
        'real_name':'lon',
        'data_len': data_len
    }
    return da_kwargs

#make suer this is well commented, instead of 
class ToyIndex_scalar(xr.Index): #customindex inherits xarray Index
    def __init__(self, x_indexes, variables=None): #added =None trying to fix .join(), 7/9
        
        self.indexes = variables
        self._xindexes = x_indexes 
        if variables is not None:

            self.spatial_ref = variables['spatial_ref']
        else:
            self.spatial_ref = None
    @classmethod          
    def from_variables(cls,variables, **kwargs):
        '''this method creates a ToyIndex obj from a variables object.
        variables created like this:
        coord_vars = {name:ds._variables[name] for name in coord_names}
        coord_names is passed to set_xindex
        '''
        #print('variables ', variables)
        assert len(variables) == 2
        assert 'x' in variables
        assert 'spatial_ref' in variables 
        
        dim_variables = {}
        scalar_vars = {}
        for k,i in variables.items():
            if variables[k].ndim ==1:
                dim_variables[k] = variables[k]
            if variables[k].ndim ==0:
                scalar_vars[k] = variables[k]
        
        options = {'dim':'x',
                   'name':'x'}
        
        x_indexes = {
            k: PandasIndex.from_variables({k: v}, options = options) 
            for k,v in dim_variables.items()
        }
        
        x_indexes['spatial_ref'] = variables['spatial_ref']
        
        return cls(x_indexes, variables)
    
    def create_variables(self, variables=None):
        '''creates coord variable from index'''
        if not variables:
            variables = self.joined_var

        idx_variables = {}
        

        for index in self._xindexes.values():
            #want to skip spatial ref
            if type(index) == xr.core.variable.Variable:
                pass
            else:

                x = index.create_variables(variables)
                idx_variables.update(x)
                
        idx_variables['spatial_ref'] = variables['spatial_ref']          
        return idx_variables

    def transform(self, value):
        
        #extract attrs
        fac = self.spatial_ref.attrs['factor']
        key = self.spatial_ref.attrs['idx_name']

        #handle slice
        if isinstance(value, slice):
            
            start, stop, step = value.start, value.stop, value.step
            new_start, new_stop, new_step = start / fac, stop/fac, step
            new_val = slice(new_start, new_stop, new_step)
            transformed_labels = {key: new_val}
            return transformed_labels
        
        #single or list of values
        else:
        
            vals_to_transform = [] 

            if not isinstance(value, Sequence):
                value = [value]

            for k in range(len(value)):

                val = value[k]
                vals_to_transform.append(val)

            #logic for parsing attrs, todo: switch to actual transform
            transformed_x = [int(v / fac) for v in vals_to_transform]
            transformed_labels = {key:transformed_x}
            return transformed_labels

    def sel(self, labels):
        
        assert type(labels) == dict

        #user passes to sel
        label = next(iter(labels.values()))
        #materialize coord array to idx off of
        params = self.spatial_ref.attrs['range']
        full_arr = np.arange(params[0], params[1], params[2])
        toy_index = PandasIndex(full_arr, dim='x')

        #transform user labesl to coord crs
        idx = self.transform(label)
        #sel on index created in .sel()
        matches = toy_index.sel(idx)

        return matches 
        

    def equals(self, other):
        
        result = self._xindexes['x'].equals(other._xindexes['x']) and self._xindexes['spatial_ref'].equals(other._xindexes['spatial_ref'])
        
        return result

    def join(self, other, how='inner'):
        '''I struggled with this and feel like its pretty hacky. it doesn't fully get away from needing x 
        but it constructs indexes used in joins from attrs (for self, not other) 
        steps in this function:
        1. for self, extract 'range' metadata from spatial_ref attrs. 
            - expand 'range' into an array and make a pandas index from it
        2. now, need range info from 'other' (this i'm not remembering exactly what i was thinking. 
            - goal is to get away from using 'x' coord var (ie. create index from a range), but this still uses 'x' to create range
            - from other, extract start, stop and solve for x from xindexes['x'].index
            - create array and pandasindex from range params
        3. now that we have self and other indexes, join them to create new_indexes
        4. in align, create_variables() will be called after the join, 
            so new_indexes needs accurate spatial_ref metadata to create the new index variable 
            (note, not rememberign exactly what I was thinking when I wrote this, feels circular)
        '''

        #make self index obj
        params_self = self.spatial_ref.attrs['range']
        print(' self range ', params_self)
        full_arr_self = np.arange(params_self[0], params_self[1], params_self[2])
        toy_index_self = PandasIndex(full_arr_self, dim='x')
        

        #make other index obj
        other_start = other._xindexes['x'].index.array[0]
        other_stop = other._xindexes['x'].index.array[-1]
        other_step = np.abs(int((other_start-other_stop) / (len(other._xindexes['x'].index.array)-1)))
        print('other range ', other_start, other_stop, other_step)
        
        params_other = other.spatial_ref.attrs['range']
        full_arr_other = np.arange(other_start, other_stop, other_step) #prev elements of params_other
        toy_index_other = PandasIndex(full_arr_other, dim='x')
        
        self._indexes = {'x': toy_index_self}
        other._indexes = {'x':toy_index_other}
        
        
        new_indexes = {'x':toy_index_self.join(toy_index_other, how=how)}
        
        #need to return a ToyIndex obj, but don't want to have to pass variables
        # so need to add all of the things that ToyIndex needs to new_indexes before passign it to return?
        
        #this will need to be generalized / testsed more
        new_indexes['spatial_ref'] =  deepcopy(self.spatial_ref) #this needs to get updated wtih new range ? 
        start = int(new_indexes['x'].index.array[0])
        stop = int(new_indexes['x'].index.array[-1])
        step = int((stop-start) / (len(new_indexes['x'].index.array) -1))
        
        new_indexes['spatial_ref'].attrs['range'] = [start, stop, step]
        
        idx_var = xr.IndexVariable(dims=new_indexes['x'].index.name,
                                   data = new_indexes['x'].index.array)
        attr_var = new_indexes['spatial_ref']
        print('attr_var type ', type(attr_var))              
        idx_dict = {'x':idx_var, 
                   'spatial_ref':attr_var}
        
        new_obj = type(self)(new_indexes)
        new_obj.joined_var = idx_dict
        return new_obj
        

    def reindex_like(self, other, method=None, tolerance=None):

        params_self = self.spatial_ref.attrs['range']
        full_arr_self = np.arange(params_self[0], params_self[1], params_self[2])
        toy_index_self = PandasIndex(full_arr_self, dim='x')
       
        toy_index_other = other._xindexes['x']
    
        d = {'x': toy_index_self.index.get_indexer(other._xindexes['x'].index, method, tolerance)}
               
        return d
        
     