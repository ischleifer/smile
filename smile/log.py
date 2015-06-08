#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the smile package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


import sqlite3

class LogExperiment(object):
    experiment_pk = property()
    experiment_name = property()
    group_domain = property()

class LogSubject(object):
    subject_pk = property()
    experiment = property()
    subject_id = property()
    
    def __getattr__(self, name):
        raise NotImplementedError

    def __setattr__(self, name, value):
        raise NotImplementedError

class LogSession(object):
    session_pk = property()
    experiment = property()
    paradigm_name = property()
    paradigm_version = property()
    subject = property()
    session_title = property()
    start_time = property()
    stop_time = property()
    host_name = property()
    user_name = property()
    experimenter = property()

#TODO: auxiliary files

class LogDB(object):
    def get_experiment(self, experiment_name):
        raise NotImplementedError
    
    def get_subject(self, subject_id):
        raise NotImplementedError

    def new_session(self, **attributes):
        raise NotImplementedError
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!




    def run_modification(self, query, params, blocking=False):
        raise NotImplementedError

    def iter_select(self, query, params, order_by=None):
        raise NotImplementedError

    def scalar_select(self, query, params):
        raise NotImplementedError

    def add_event_table(self, table_name, type_dict):
        column_names = type_dict.keys()
        type_map = {
            bool : "BOOLEAN",
            int : "INTEGER",
            float : "REAL",
            str : "TEXT"}
        column_defs = ["%s %s" % (name, type_map[type_]) for
                       name, type_ in type_dict.items()]
        query = "CREATE TABLE IF NOT EXISTS %s (%s);" % (
            table_name,
            ",".join(column_defs))
        #TODO: params!
        self.run_modification(self, query, params, blocking)

    def add_event(self, table_name, session, event_title, timestamp, value_dict,
                  blocking=False):
        #TODO: table creation???
        values = {
            "SESSION_PK" : session.session_pk,
            "TITLE" : session.session_title,
            "TIMESTAMP" : timestamp,  #???
            }
        values.update(value_dict)
        query = "INSERT INTO %s (%s) VALUES (%s);" % (
            table_name,
            ",".join(values.keys()),
            ",".join("?" * len(values)))
        params = values.values()
        self.run_modification(self, query, params, blocking)

    def get_filters(self, experiment=None, subject=None, session_title=None):
        filters = []
        params = []
        if experiment is not None:
            filters.append("EXPERIMENT.PK=%d" % experiment.experiment_pk)
        if subject is not None:
            filters.append("SUBJECT.PK=%d" % subject.subject_pk)
        if session_title is not None:
            filters.append("SESSION.TITLE=?")
            params.append(session_title)
        #TODO: subject demographics?
        return filters, params

    #TODO: look things up by name

    def get_session_selection(self, experiment=None, subject=None,
                              session_title=None):
        filters, params = self.get_filters(experiment, subject, session_title)
        filters = ["SESSION.SUBJECT_PK=SUBJECT.PK",
                   "SESSION.EXPERIMENT_PK=EXPERIMENT.PK"] + filters
        tables = "SESSION, SUBJECT, EXPERIMENT"
        where = " AND ".join(filters)
        return ("FROM %s WHERE %s " +
                "ORDER BY SESSION.START_TIME;") % (tables, where), params

    def get_subject_selection(self, experiment=None, session_title=None):
        filters, params = self.get_filters(experiment, None, session_title)
        filters = ["SUBJECT.PK=SESSION.SUBJECT_PK",
                   "SESSION.EXPERIMENT_PK=EXPERIMENT.PK"] + filters
        tables = "SUBJECT, SESSION, EXPERIMENT"
        where = " AND ".join(filters)
        return "FROM %s WHERE %s ORDER BY SUBJECT.ID;" % (tables, where), params

    def get_experiment_selection(self, subject=None):
        filters, params = self.get_filters(None, subject, None)
        filters = ["SUBJECT.PK=SESSION.SUBJECT_PK"
                   "EXPERIMENT.PK=SESSION.EXPERIMENT_PK"] + filters
        tables = "SESSION, SUBJECT, EXPERIMENT"
        where = " AND ".join(filters)
        return ("FROM %s WHERE %s " +
                "GROUP BY SUBJECT.PK " +
                "ORDER BY EXPERIMENT.NAME;") % (tables, where), params

    def iter_sessions(self, experiment=None, subject=None, session_title=None):
        selection, params = self.get_session_selection(experiment, subject,
                                                       session_title)
        query = "SELECT SESSION.PK %s;" % selection
        for record in self.iter_select(query, params):
            yield LogSession(self, record[0])

    def count_sessions(self, experiment=None, subject=None, session_title=None):
        selection, params = self.get_session_selection(experiment, subject,
                                                       session_title)
        query = "SELECT COUNT(*) %s;" % selection
        return self.scalar_select(query, params)

    def iter_subjects(self, experiment=None, session_title=None):
        selection, params = self.get_subject_selection(experiment,
                                                       session_title)
        query = "SELECT SUBJECT.PK %s;" % selection
        for record in self.iter_select(query, params):
            yield LogSubject(self, record[0])

    def count_subjects(self, experiment=None, session_title=None):
        selection, params = self.get_subject_selection(experiment,
                                                       session_title)
        query = "SELECT COUNT(*) %s;" % selection
        return self.scalar_select(query, params)

    def iter_experiments(self, subject=None):
        selection, params = self.get_experiment_selection(subject)
        query = "SELECT EXPERIMENT.PK %s;" % selection
        for record in self.iter_select(query, params):
            yield LogExperiment(self, record[0])

    def count_experiments(self, subject=None):
        selection, params = self.get_experiment_selection(subject)
        query = "SELECT COUNT(*) %s;" % selection
        return self.scalar_select(query, params)

    def iter_event_titles(self):
        raise NotImplementedError

    def count_event_titles(self):
        raise NotImplementedError

    def iter_events(self, event_title=None, session=None, session_title=None,
                    subject=None, experiment=None):
        raise NotImplementedError

    def count_events(self, event_title=None, session=None, session_title=None,
                     subject=None, experiment=None):
        raise NotImplementedError

    def vacuum(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def summarize(self, dest_file, experiment=None, subject=None, session=None,
                  session_title=None, event_title=None):
        pass #...

    def event_csv(self, dest_file, event_title, experiment=None, subject=None,
                  session=None, session_title=None, numeric_only=False):
        pass #...

    #TODO: data by subject demographics?

    #TODO: copying between DBs, deletion
    #...









import yaml
import csv
#import sys

# set up a dumper that does not do anchors or aliases
if hasattr(yaml,'CSafeDumper'):
    Dumper = yaml.CSafeDumper
else:
    Dumper = yaml.SafeDumper
Dumper.ignore_aliases = lambda self, data: True
def dump(logline, stream=None):
    return yaml.dump(logline, stream, Dumper=Dumper)

# for eventually writing CSV files with headers
# from: http://stackoverflow.com/questions/2982023/writing-header-in-csv-python-with-dlictwriter
"""
from collections import OrderedDict
ordered_fieldnames = OrderedDict([('field1',None),('field2',None)])
with open(outfile,'wb') as fou:
    dw = csv.DictWriter(fou, delimiter='\t', fieldnames=ordered_fieldnames)
    dw.writeheader()
    # continue on to write data
"""
def load_yaml(yaml_file, **append_cols):
    # load the dictlist
    dictlist = yaml.load(open(yaml_file,'r'))
    if dictlist is None:
        return []
    for i in range(len(dictlist)):
        dictlist[i].update(append_cols)
    return dictlist

def unwrap(d, prefix=''):
    """
    Process the items of a dict and unwrap them to the top level based
    on the key names.
    """
    new_item = {}
    for k in d:
       	# add prefix
    	key = prefix+k
        
        # see if dict
        if isinstance(d[k],dict):
            new_item.update(unwrap(d[k],prefix=key+'_'))
            continue

        # see if tuple
        if isinstance(d[k],tuple):
            # turn into indexed dict
            tdict = {}
            for j in range(len(d[k])):
                tdict[str(j)] = d[k][j]
            new_item.update(unwrap(tdict,prefix=key+'_'))
            continue

        # just add it in
        new_item[key] = d[k]

    return new_item
    
def yaml2dl(yaml_file, **append_cols):
    # load in the yaml as a dict list
    dl = load_yaml(yaml_file, **append_cols)

    # loop over each kv pair and unwrap it
    for i in xrange(len(dl)):
        dl[i] = unwrap(dl[i])

    return dl

def yaml2csv(dictlist, csv_file, **append_cols):
    # see if dictlist is a yaml file
    if isinstance(dictlist,str):
        # assume it's a file and read it in
        # get the unwraped dict list
        dictlist = yaml2dl(dictlist, **append_cols)
    dl = dictlist

    if len(dl) == 0:
        return

    # get all unique colnames
    colnames = []
    for i in range(len(dl)):
        for k in dl[i]:
            if not k in colnames:
                colnames.append(k)
                      
    # write it out
    with open(csv_file, 'wb') as fout:
        # create file and write header
        dw = csv.DictWriter(fout, fieldnames=colnames)
        dw.writeheader()
        # continue on to write data
        dw.writerows(dl)

