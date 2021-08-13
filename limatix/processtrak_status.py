from __future__ import print_function

import sys
import os
import os.path
import posixpath
import socket
import copy
import inspect
import numbers
import traceback
import collections
import ast
import hashlib
import binascii
import datetime

from lxml import etree

try:
    from cStringIO import StringIO
    pass
except ImportError:
    from io import StringIO
    pass


import shutil
import datetime
import subprocess

try:
    # py2.x
    from urllib import pathname2url
    from urllib import url2pathname
    from urllib import quote
    from urllib import unquote
    from urlparse import urlparse
    from urlparse import urlunparse
    from urlparse import urljoin    
    pass
except ImportError:
    # py3.x
    from urllib.request import pathname2url
    from urllib.request import url2pathname
    from urllib.parse import quote
    from urllib.parse import unquote
    from urllib.parse import urlparse
    from urllib.parse import urlunparse
    from urllib.parse import urljoin
    pass

try: 
    import builtins  # python3
    pass
except ImportError: 
    import __builtin__ as builtins # python2
    pass

if not hasattr(builtins,"unichr"):
    # python3
    unichr=chr
    pass

if not hasattr(builtins,"unicode"):
    # python3
    unicode=str
    pass


# import lm_units

from . import timestamp
from . import canonicalize_path
from .canonicalize_path import etxpath2human

from . import dc_value as dcv
from . import provenance as provenance
from . import xmldoc
from . import processtrak_prxdoc
from . import processtrak_common
from . import processtrak_procstep
from . import timestamp as lm_timestamp





def eval_status_inputfile(inputfile,inputfile_href,prxdoc,prxfilehref,outputdict,all_step_elements):
    """inputfile and  inputfile_href are the name and href for the inputfile experiment log.

    outputdict is the output of processtrak_common.build_outputdict(prxdoc,inputfiles_with_hrefs).

    all_step_elements is a list of all step elements from the .prx file

    NOTE THAT SINCE THIS FUNCTION OPENS OUTPUT FILES in read-only mode, you MUST NOT EXECUTE STEPS based on 
    outputdict afterward without resetting it first (see processtrak_common: reset_outputdict())

    Look at provenance tags to see which steps have been run
    ... This results in actionproc_date_status_success_dict_matching_prxfile
    which is a dictionary by stepname of (actionproc (lip:process element),
                                          date (timestamp string),
                                          outoforder (True, False),
                                          xpath filter flag (True/False for additional filters),
                                          success (True/False for apparently successful run)
                                          execution needed (True/False)

    """
    
    
    outdoc = outputdict[inputfile_href]
    # NOTE: calling open_or_lock_output with readonly=True means it's NOT OK
    # to actually execute anything with this outdoc in the outputdict, as
    # the output will be only opened as read-only
    if os.path.exists(outdoc.outputfilehref.getpath()):
        processtrak_common.open_or_lock_output(prxdoc,outdoc,readonly=True)
        xlpdocu=outdoc.output
        pass
    else:
        xlpdocu=None
        pass
    
    try: 
    
        if xlpdocu is not None:
            # Find all lip:process tags with an action child that also have-- either themselves or and ancestor -- a wascontrolledby with a lip:prxfile 
            actionprocesses=xlpdocu.xpath("lip:process/descendant-or-self::lip:process[lip:action and (ancestor-or-self::lip:process/lip:wascontrolledby)[1]/lip:prxfile/@xlink:href]")
            
            actionprocs_with_prxfile=[ (actionproc,xlpdocu.xpathsinglecontext(actionproc,"(ancestor-or-self::lip:process/lip:wascontrolledby)[1]/lip:prxfile")) for actionproc in actionprocesses ]
            
            actionprocs_with_prxfilehref=[ (actionproc, dcv.hrefvalue.fromxml(xlpdocu,prxfile)) for (actionproc,prxfile) in actionprocs_with_prxfile ]
            
            actionprocs_matching_prxfile = [ actionproc for (actionproc,actionprxfilehref) in actionprocs_with_prxfilehref if actionprxfilehref==prxfilehref ]
            actionprocs_not_matching_prxfile = [ actionproc for (actionproc,actionprxfilehref) in actionprocs_with_prxfilehref if not(actionprxfilehref==prxfilehref) ]
            
            actionproc_listdict_matching_prxfile = { }  # dictionary by step name of lists of actionprocs 
            for actionproc in actionprocs_matching_prxfile:
                stepname = xlpdocu.xpathsinglecontextstr(actionproc,"lip:action")
                if stepname not in actionproc_listdict_matching_prxfile:
                    actionproc_listdict_matching_prxfile[stepname] = [] # empty list
                    pass
                
                actionproc_listdict_matching_prxfile[stepname].append(actionproc)
                pass
        
            
            # sort lists in actionproc_listdict_matching_prxfile[stepname] by starttimestamp
            
            for stepname in actionproc_listdict_matching_prxfile:  # dictionary by step name of lists of actionprocs
                actionproc_listdict_matching_prxfile[stepname].sort(key = lambda actionproc: xlpdocu.xpathsinglecontextstr(actionproc,"lip:starttimestamp"))
                pass
            
            # reduce actionproc_listdict_matching_prxfile to most recent runs (last entries)
            actionproc_dict_matching_prxfile = { stepname: actionproc_listdict_matching_prxfile[stepname][-1] for stepname in actionproc_listdict_matching_prxfile }
            
            actionproc_date_success_dict_matching_prxfile = { stepname: (actionproc_dict_matching_prxfile[stepname], # actionproc
                                                                         xlpdocu.xpathsinglecontextstr(actionproc_dict_matching_prxfile[stepname],"lip:starttimestamp"), # start timestamp
                                                                         "-l" in ast.literal_eval(xlpdocu.xpathsinglecontextstr(actionproc_dict_matching_prxfile[stepname],"lip:argv",default="[ ]")),  # Presence of additional xpath filters when running this step
                                                                         len(xlpdocu.xpathcontext(actionproc_dict_matching_prxfile[stepname],"descendant-or-self::lip:log[@status != 'success']")) > 0 or len(xlpdocu.xpathcontext(actionproc_dict_matching_prxfile[stepname],"descendant-or-self::lip:process[count(lip:finishtimestamp) = 0]")) > 0)  # failure indicator: status not listed as success or no finish timestamp
                                                              for stepname in actionproc_listdict_matching_prxfile }
            
            
            
            
            
        
            
            pass
        else:
            
            #actionprocs_with_prxfile = []
            actionproc_date_success_dict_matching_prxfile = {}
            actionprocs_not_matching_prxfile = []
            pass
        
        
        most_recent_time = datetime.datetime(1970,1,1,0,0,0,tzinfo=timestamp.UTC())  # Beginning of UNIX epoch: essentially -infinity
        
        neededflag=False
        
        actionproc_date_status_success_dict_matching_prxfile=collections.OrderedDict()
        for step_el in all_step_elements:
            
            if step_el is None:   # "None" means the copyinput step
                stepname="mergeinput" # use "mergeinput" instead of copyinput because we want the most recent (see fallback below)
                step_valid_for_inputfile = True
                pass
            else:
                stepname=processtrak_prxdoc.getstepname(prxdoc,step_el)

                script_el=prxdoc.xpathsinglecontext(step_el,"prx:script")
                step_valid_for_inputfile = processtrak_procstep.check_inputfilematch(prxdoc,step_el,script_el,inputfile_href)
                pass
            
            if not step_valid_for_inputfile:
                continue

            stepname_not_found = stepname not in actionproc_date_success_dict_matching_prxfile

            if stepname_not_found and stepname=="mergeinput":
                # try copyinput insted of mergeinput
                stepname = "copyinput"
                stepname_not_found = stepname not in actionproc_date_success_dict_matching_prxfile
                
            
            if stepname_not_found:
                neededflag=True
                actionproc_date_status_success_dict_matching_prxfile[stepname]=(None,None,True,False,False,neededflag)
                pass
            else:
                # Did find record of step having been run
                
                (actionproc,date,filterflag,failure) = actionproc_date_success_dict_matching_prxfile[stepname]
                
                parseddate = timestamp.readtimestamp(date)
                if (parseddate <= most_recent_time):
                    outoforderflag=True
                    neededflag=True
                    pass            
                else:
                    outoforderflag=False
                    most_recent_time=parseddate
                    pass

                if filterflag or failure:
                    neededflag=True
                
                actionproc_date_status_success_dict_matching_prxfile[stepname]=(actionproc,date,outoforderflag,filterflag,failure,neededflag)
                del actionproc_date_success_dict_matching_prxfile[stepname] # mark as shown
                
                pass
            pass
        
        actionprocs_missing_from_prx = actionproc_date_success_dict_matching_prxfile # whatever remains in the dictionary:

        if "copyinput" in actionprocs_missing_from_prx:
            # ignore "copyinput" because we already listed the copy step as "mergeinput"
            del actionprocs_missing_from_prx["copyinput"]
            pass
        
        # (actionproc,date,filterflag,failureflag)
        pass
    finally:
        if xlpdocu is not None:
            xlpdocu.unlock_ro()
            pass
        pass
    
        
    return (actionproc_date_status_success_dict_matching_prxfile,actionprocs_missing_from_prx,actionprocs_not_matching_prxfile)

def print_status(inputfiles_with_hrefs,prxdoc,prxfilehref,all_step_elements,ignore_locking):
    """inputfiles_with_hrefs is a list of (inputfile, inputfile_href) tuples, 
    where inputfile is the name of an experiment log for which we want status.

    all_step_elements is a list of step elements from the .prx files representing the steps of interest

    """

    # Build private dictionary by input file of output files
    outputdict=processtrak_common.build_outputdict(prxdoc,inputfiles_with_hrefs,ignore_locking)
    
    for (inputfile,inputfile_href) in inputfiles_with_hrefs:

        (actionproc_date_status_success_dict_matching_prxfile,
         actionprocs_missing_from_prx,
         actionprocs_not_matching_prxfile)=eval_status_inputfile(inputfile,
                                                                 inputfile_href,
                                                                 prxdoc,prxfilehref,
                                                                 outputdict,
                                                                 all_step_elements)
        
        print("")

        mergeinput_flag = False
        
        print("Input file: %s" % (inputfile_href.humanurl()))
        print("---------------------------")            

        xlpdocu=outputdict[inputfile_href].output
        
        
        
        for step_el in all_step_elements:
            if step_el is None:   # "None" means the copyinput step
                stepname="mergeinput" # use "mergeinput" as we want to find that if present
                pass
            else:
                stepname=processtrak_prxdoc.getstepname(prxdoc,step_el)
                pass

            stepname_not_found = not stepname in actionproc_date_status_success_dict_matching_prxfile

            if stepname_not_found and stepname=="mergeinput":
                # try copyinput as alternative
                stepname="copyinput"
                stepname_not_found = not stepname in actionproc_date_status_success_dict_matching_prxfile
                pass
            
            if stepname_not_found:
                # if eval_status_inputfile() filtered the step name from 
                # actionproc_date_status_success_dict_matching_prxfile then
                # that means the step was not applicable to this inputfile
                continue

            if stepname=="mergeinput":
                mergeinput_flag=True
                pass
            
            if xlpdocu is None:
                print("%20s NOT_EXECUTED NEEDED" % (stepname))
                pass
            else:
                # have an xlp document

                (actionproc,date,outoforderflag,filterflag,failure,needed)=actionproc_date_status_success_dict_matching_prxfile[stepname]
                if actionproc is None:                
                    print("%20s NOT_EXECUTED NEEDED" % (stepname))
                    pass
                else:
                    flagstr=""

                    if outoforderflag:
                        flagstr += " OUT_OF_ORDER"
                        pass
                    
                    if filterflag:
                        flagstr +=" USED_XPATH_FILTERS"
                        pass
                    
                    if failure:
                        flagstr += " FAILURE"
                        pass

                    if needed:
                        flagstr += " NEEDED"
                        pass

                    print("%20s %36s %s" % (stepname,date,flagstr))
                pass
            
            pass
        if len(actionprocs_missing_from_prx.keys()) > 0:
            print(" ")
            print("Additional steps not found in .prx file")
            print("---------------------------------------")
            
            for stepname in actionprocs_missing_from_prx:
                print("%20s" % (stepname))
                pass
            pass
        
        if len(actionprocs_not_matching_prxfile) > 0:
            print(" ")
            print("Additional steps from different .prx file")
            print("---------------------------------------")
            
            try:
                xlpdocu.lock_ro()
                for actionproc in actionprocs_not_matching_prxfile:
                    stepname = xlpdocu.xpathsinglecontextstr(actionproc,"lip:action")
                    print("%20s" % (stepname))
                    pass
                pass
            finally:
                xlpdocu.unlock_ro()
                pass
            
            

            pass
        if mergeinput_flag:
            print("")
            print("WARNING: mergeinput step was used. For maximum reliability recommend")
            print("         rerunning with copyinput step")
            pass
        
        
        pass
        
    
    processtrak_common.reset_outputdict(prxdoc,outputdict,previous_readonly=True) # reset our private outputdict (close all XML files) 
    pass
        
