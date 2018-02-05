import sys
import time
import logging
import os
import xml.etree.ElementTree as ET

class Config():
    configfilepath =  ".//config.xml"
    def __init__(self):
        global filepath
        global filepattern
        if ( os.path.exists( self.configfilepath ) ):
            try:
                print("config file path exists and is:", self.configfilepath)
                tree = ET.parse(self.configfilepath)
                root = tree.getroot()
            except:
                print("config file not exist")

            self.dictdir = tree.find('dictionary').find('file').find('dir').text
            print("dictdir is:", self.dictdir)
    def get_dictdir(self):
        return self.dictdir