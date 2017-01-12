#!/usr/bin/env python
"""Provide code to build a DAG from the CRF branching-logic information."""

# Imports
from collections import namedtuple

import pandas as pd
import numpy as np

import networkx as nx

from munch import Munch

# Metadata
__author__ = "Gus Dunn"
__email__ = "w.gus.dunn@gmail.com"

EdgeLabel = namedtuple(typename='EdgeLabel', field_names=["n1", "n2", "label"], verbose=False, rename=False)

# Functions
def load_data_dict(data_dict_):
    """Load data dict into df."""
    return pd.read_csv(data_dict_)
    
def make_edges(data_dict):
    """Return df with just columns that represent edges."""
    rename = {'Variable / Field Name':'field_name',
              'Branching Logic (Show field only if...)':'branch_logic'}
    
    return data_dict[['Variable / Field Name','Branching Logic (Show field only if...)']].rename(columns=rename)
    
    
def make_field_map(data_dict):
    """Return Dict to translate field names and field labels."""
    d = Munch()
    field_names = data_dict['Variable / Field Name'].values
    field_labels = data_dict['Field Label'].values
    
    d = Munch({k:v for k,v in zip(field_names, field_labels)})
    d.update(Munch({d:l for d,l in zip(field_labels, field_names)}))
    
    return d
    
    
def make_top_level_nodes_and_others(edges_raw):
    """Return dict of `top_level_nodes`,`lower_edges_raw`."""
    d = Munch()
    
    tln = edges_raw.branch_logic.apply(lambda v: pd.isnull(v))
    
    d.top_level_nodes = edges_raw.field_name[tln]
    d.lower_edges_raw = edges_raw[~tln]
    
    return  d

def parse_branch_logic(logic):
    """Return `n1`, `label` based on a single branch logic string."""
    n1, label = logic.replace('[','').replace(']','').replace("'","").split(' = ')
    
    if '(' in n1:
        n1, label = n1.replace(')','').split('(')
        
    return n1, label
    

def make_lower_edges(lower_edges_raw):
    """Yield named tuples ("n1", "n2", "label") based on branch logic."""
    field_name, branch_logic = 0,1
    
    for row in lower_edges_raw.values:
        
        try:
            n1, label = parse_branch_logic(logic=row[branch_logic])
            n2 = row[field_name]
            yield EdgeLabel(n1=n1,n2=n2,label=label)
            
        except ValueError as exc:
            if ' or ' in row[branch_logic]:
                logics = [l for l in row[branch_logic].split(' or ')]
                n2 = row[field_name]
                
                for parsed_logic in [parse_branch_logic(logic=l) for l in logics]:
                    n1, label = parsed_logic
                    yield EdgeLabel(n1=n1,n2=n2,label=label)
            

def add_lower_edges(g,lower_edges_raw):
    """Add lower level nodes with edge labels."""
    for e in make_lower_edges(lower_edges_raw):
        g.add_edge(u=e.n1, v=e.n2, label=e.label)
        
    
def add_top_level_edges(g,top_level_nodes):
    """Add top l;evel nodes top graph."""
    l = len(top_level_nodes)
    
    tle = zip(['start']*l,
              top_level_nodes)
    
    g.add_edges_from(ebunch=tle)