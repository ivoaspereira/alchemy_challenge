#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 17 14:59:41 2018

@author: ivo
"""
import csv
import codecs
import os
import glob
import json
from enum import Enum
from io import StringIO
import pandas as pd

class Fauxlizer(object):
    """ Constructor with one parameter.
        :param filename: path to CSV file.
    """
    def __init__(self, filename):
        self.filename = filename
        
    """ Method returning a dictionary of the CSV file. """
    def _open_csv(self):
        return csv.DictReader(codecs.open(self.filename, "r", encoding='utf-8', errors='ignore'), delimiter=",")
        
    """ Method to parse the CSV file and validate it according to requirements.
        Defines an array of columns to allow easy scalability.
        Handles exceptions to allow better performance.
        It returns False and exception details as soon as validation fails.
        :return: True if the CSV file is valid, False if it is not valid.
    """
    def parse_validate(self):
        # Using a dictionary assuming that there is no problem having columns in different order
        columns = ['experiment_name', 'sample_id', 'fauxness', 'category_guess']
        self.valid = True
        try:
            rows = self._open_csv()
            row_count = 0
            for row in rows:
                row_count+=1
                for column in columns:
                    method_name = '_validate_' + str(column)
                    method = getattr(self, method_name)
                    if not method(row[column],row_count):
                        self.valid = False
                        break
            print("File ",self.filename," is valid")
        except Exception as e:
            print("File ",self.filename," not valid. Exception: ", e)
            self.valid = False
        
        return self.valid
        
    """ Validates the CSV file according to experiment_name column requirements.
        Throws and exception if data is not valid.
        :param data: the value to validate.
        :row_number: the respective row number (for error handling).
        :return: True if data is valid, False if it is not valid.  
    """
    def _validate_experiment_name(self, data, row_number):
        if not data:
            raise Exception('ExperimentNameNotValid',data,row_number)
            return False
        return True

    """ Validates the CSV file according to sample_id column requirements.
        Throws and exception if data is not valid.
        :param data: the value to validate.
        :row_number: the respective row number (for error handling).
        :return: True if data is valid, False if it is not valid.  
    """
    def _validate_sample_id(self, data, row_number):
        try:
            val = int(data)
            if val <= 0:
                raise Exception()
        except Exception:
            raise Exception('SampleIdNotValid',data,row_number)   
            return False
        return True
        
    """ Validates the CSV file according to fauxness column requirements.
        Throws and exception if data is not valid.
        :param data: the value to validate.
        :row_number: the respective row number (for error handling).
        :return: True if data is valid, False if it is not valid.  
    """
    def _validate_fauxness(self, data, row_number):
        try:
            val = float(data)
            if not 0.0 <= val <= 1.0:
                raise Exception
        except Exception:
            raise Exception('FauxnessNotValid',data,row_number)  
            return False
        return True
        
    """ Validates the CSV file according to category_guess column requirements.
        Throws and exception if data is not valid.
        :param data: the value to validate.
        :row_number: the respective row number (for error handling).
        :return: True if data is valid, False if it is not valid.  
    """
    def _validate_category_guess(self, data, row_number):
        categories = [item.value for item in CategoryGuess]
        if not data in categories:
            raise Exception('CategoryGuessNotValid',data,row_number)
            return False
        return True
        
    """ Method to return a summary of the CSV file in JSON format.
        Example:
            {
              "filename": "./data/file_1.faux",
              "totalRows": 10,
              "fauxness": {
                "minFauxness": 0.0359243293929,
                "maxFauxness": 0.882850918581,
                "meanFauxness": 0.4999555999134899,
                "stdFauxness": 0.2656831945156546
              },
              "category_guess": {
                "totalReal": 4,
                "totalFake": 4,
                "totalAmbiguous": 2
              }
            }
        :return: Summary in JSON if CSV file is valid, False if it is not valid.
    """
    def summary(self):
        if self.valid:
            df = pd.read_csv(self.filename)

            cat_lst = []
            for item in CategoryGuess:
                cat_lst.append(df[df['category_guess'].str.match(item.value)].shape[0])
            
            data = {
                    "filename": self.filename,
                    "totalRows": df.shape[0],
                    "fauxness": {
                            "minFauxness": df['fauxness'].min(),
                            "maxFauxness": df['fauxness'].max(),
                            "meanFauxness": df['fauxness'].mean(),
                            "stdFauxness": df['fauxness'].std()},
                    "category_guess": {
                            "totalReal": cat_lst[0],
                            "totalFake": cat_lst[1],
                            "totalAmbiguous": cat_lst[2],
                            } 
                }
            return json.dumps(data)
        else:
            return False
        
    """ Generic method to parse data from a row in a specific format.
        Calls the specific method according to the parsing format.
        :param row: index of row to parse.
        :param export_format: desired format (csv, json or python).
        :return: if CSV file is valid it returns the specific method result, False otherwise.
    """
    def get_row_data(self, row, export_format):
        if self.valid:
            method_name = '_get_row_data_' + str(export_format)
            method = getattr(self, method_name)
            return method(row)
        else:
            return False
        
    """ Parse the row to Fauxlizer's nativ CSV format. """
    def _get_row_data_csv(self, row):
        rows = self._open_csv()
        rows_list = list(rows)
        output = StringIO()
        df = pd.DataFrame.from_dict(rows_list[row], orient="index")
        df.T.to_csv(output,index=False)
        return output.getvalue()
        
    """ Parse the row to JSON format. """
    def _get_row_data_json(self, row):
        rows = self._open_csv()
        rows_list = list(rows)
        return json.dumps(rows_list[row])
        
    """ Returns a Python in-memory representation of row. """
    def _get_row_data_python(self, row):
        rows = self._open_csv()
        rows_list = list(rows)
        return rows_list[row]
    
""" Enumeration to represent possible values for category_guess column. """
class CategoryGuess(Enum):
    REAL = "real"
    FAKE = "fake"
    AMBIGUOUS = "ambiguous"
    
    
#############################################################################
###    Testing the API
#############################################################################

path = '../data/'
for filename in glob.glob(os.path.join(path, '*.faux')):
    faux = Fauxlizer(filename)
    faux.parse_validate()
    #print(faux.summary())
    
###     Test result:    
### File  ./data/file_0.faux  is valid
### File  ./data/file_1.faux  is valid
### File  ./data/file_3.faux  not valid. Exception:  'experiment_name'
### File  ./data/file_4.faux  not valid. Exception:  ('CategoryGuessNotValid', 'assay.79519/retry', 1)
### File  ./data/file_5.faux  not valid. Exception:  ('CategoryGuessNotValid', 'AMBIGUous', 1)
### File  ./data/file_6.faux  not valid. Exception:  ('ExperimentNameNotValid', '', 2)
### File  ./data/file_7.faux  not valid. Exception:  ('SampleIdNotValid', '-235800', 212)
### File  ./data/file_9.faux  is valid

#############################################################################