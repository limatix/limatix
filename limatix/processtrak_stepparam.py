from __future__ import print_function

import sys
import os
import os.path
import numbers
import copy
import ast

from . import dc_value as dcv
from .canonicalize_path import etxpath2human

try: 
    import builtins  # python3
    pass
except ImportError: 
    import __builtin__ as builtins # python2
    pass
    
if hasattr(builtins,"long"):
    int_or_long=long
    pass
else:
    int_or_long=int  # python3
    pass

if not hasattr(builtins,"basestring"):
    basestring=str  # python3
    pass


def evaluate_from_number(number,typename,paramname):
    if typename=="float":
        return float(number)
    elif typename=="complex":
        return complex(number)
    elif typename=="int":
        return int(number)
    else:
        raise ValueError("processtrak_stepparam: Error evaluating parameter %s: evaluate_from_number cannot convert number to %s" % (paramname,typename))
    
    
    pass

def evaluate_from_bool(boolean,typename,paramname,paramdebug):
    if typename=="bool":
        return bool(boolean)
    elif typename=="int":
        if paramdebug:
            print("            Interpreting boolean as integer %d" % (int(boolean)))
            pass
        return int(boolean)
    elif typename=="str":
        if paramdebug:
            print("            Interpreting boolean as string \"%s\"" % (str(boolean)))
            pass
        return str(boolean)
    else:
        raise ValueError("processtrak_stepparam: Error evaluating parameter %s: evaluate_from_bool cannot convert boolean to %s" % (paramname,typename))
    pass

def evaluate_from_string(string,typename,paramname,paramdebug):
    literal_python_typedict={
        "list": list,
        "tuple": tuple,
        "dict": dict,
        "set": set,
        "bool": bool,
    }

    if typename=="str":
        if paramdebug:
            print("            Interpreting as string")
            pass
        return str(string)
    elif typename=="int":
        if paramdebug:
            print("            Interpreting as int")
            pass
        return int(string)
    elif typename=="float":
        if paramdebug:
            print("            Interpreting as float")
            pass
        return float(string)
    elif typename=="complex":
        if paramdebug:
            print("            Interpreting as complex")
            pass
        return complex(string)
    elif typename in literal_python_typedict:
        if paramdebug:
            print("            Interpreting as literal %s" % (typename))
            pass
        return literal_python_typedict[typename](ast.literal_eval(string))
    else:
        raise ValueError("processtrak_stepparam: Error evaluating parameter %s: evaluate_from_string cannot convert string to %s" % (paramname,typename))
    pass



def evaluate_from_element(xmldocu,element,basetypename,paramname,useparamname,paramdebug):
    # basetypename can be str,float,complex,int,bool : basic Python types
    # list, tuple, dict, set : Python type interpreted by ast.literal_eval() -- may return None if that is given!
    # href, string, xmltree, numericunits, etc: dc_value types
    
    # if typename is None, then we evaluate as an element
    # if typename is "doc" then we evaluate as the document
    # containg the element, i.e. xmldocu, -- which for <param> elements in prx file is prxdoc
    # (i.e.. the document that contains the element)
        
    basic_python_typedict={
        "str": str,
        "float": float,
        "complex": complex,
        "int": int_or_long,
    }
    literal_python_typedict={
        "list": list,
        "tuple": tuple,
        "dict": dict,
        "set": set,
        "bool": bool,
    }


    if basetypename in basic_python_typedict:
        if paramdebug:
            print("        Found single element %s with value %s; cast to type %s" % (useparamname,xmldocu.gettext(element),basetypename))
            pass
        return basic_python_typedict[basetypename](xmldocu.gettext(element))
    elif basetypename in literal_python_typedict:


        if paramdebug:
            print("        Found single element %s with value %s; cast to type %s" % (useparamname,xmldocu.gettext(element),basetypename))
            pass

        valuetext = xmldocu.gettext(element)        
        # accommodate inconsistency between case of 
        # XPath true/false vs. Python True/False
        if basetypename=="bool" and valuetext == "true":
            valuetext="True"
            pass
        elif basetypename=="bool" and valuetext == "false":
            valuetext="False"
            pass

        return literal_python_typedict[basetypename](ast.literal_eval(valuetext))
    elif basetypename is None:
        if paramdebug:
            print("        Found single %s element as node" % (useparamname))
            pass
        return element
    elif basetypename+"value" in dir(dcv) and issubclass(getattr(dcv,basetypename+"value"),dcv.value):
        if paramdebug:
            print("        Interpreting single %s element as single element of dcv.%svalue" % (useparamname,basetypename))
            pass
        return getattr(dcv,basetypename+"value").fromxml(xmldocu,element)
    elif basetypename=="doc":
        if paramdebug:
            print("        returning containing document")
            pass
        return xmldocu
    
    raise NameError("Unknown typename \"%s\" evaluating %s" % (basetypename,paramname))



    

def evaluate_from_elements(xmldocu,elementlist,typename,paramname,useparamname,paramdebug):
    # typename can be basetypename from evaluate_from_element (above)
    # can also be basetype from evaluate_from_element followed by "list"
    # can also be "nodeset"

    if typename is not None and len(typename) > 4 and typename.endswith("list"):
        # NOTE: Just bare "list" interpreted directly in evaluate_from_element with ast.parse()...
        # if you want a list of nodes, specify as "nodeset"
        basetypename=typename[:-4]
        listflag=True
        if paramdebug:
            print("        Parameter %s interpreted as a list of %s" % (paramname,basetypename))
            pass
        pass
    else:
        basetypename=typename
        listflag=False
        pass

    if basetypename=="nodeset":
        # Directly handle nodeset"
        if listflag:
            raise ValueError("In parameter %s: nodeset is already a list; should not use list suffix" % (paramname))
        if paramdebug:
            print("        Found %d %s elements as node-set" % (len(elementlist),useparamname))
            pass
        
        
        return elementlist
    elif listflag:
        # Iterate over element list if given "list" suffix
        retlist = []
        for element in elementlist:
            retlist.append(evaluate_from_element(xmldocu,element,basetypename,paramname,useparamname,paramdebug))
            pass
        return retlist
    else:
        # Single element: elementlist should be length 1

        if len(elementlist) > 1:
            raise ValueError("Got %d values for parameter %s" % (len(elementlist),paramname))
        elif len(elementlist) == 0:
            raise NameError("No element found for parameter %s" % (paramname))
        else:

            return evaluate_from_element(xmldocu,elementlist[0],basetypename,paramname,useparamname,paramdebug)
        pass
    pass

class stepparam(object):
    name=None
    prxdoc=None
    element=None  # element in prxdoc
    

    def __init__(self,**kwargs): # supply name and value
        self.textflag=False
        self.values=[]

        for argname in kwargs:
            if argname=="value":
                self.values.append(kwargs[argname])
                pass
            else :
                setattr(self,argname,kwargs[argname])
                pass
            pass
        pass

    def get_xpath_variables(self,outdoc,inputfilehref):

        variables = {"outputfile":outdoc.get_filehref().get_bare_unquoted_filename(),
                     "outputfileurl":outdoc.get_filehref().absurl(),
                     "inputfile":inputfilehref.get_bare_unquoted_filename(),
                     "inputfileurl":inputfilehref.absurl(),
        }
        
        
        return variables

    def get_element_namespaces(self):
        namespaces=copy.deepcopy(self.element.nsmap)
        if None in namespaces:
            del namespaces[None]
            pass
        return namespaces
    
    def test_condition(self,outdoc,element,inputfilehref,paramdebug):
        if not self.prxdoc.hasattr(self.element,"condition"):
            if paramdebug:
                print("    Parameter %s is unconditional" % (self.name))
                pass
            return True
        
        condition=self.prxdoc.getattr(self.element,"condition")

        if paramdebug:
            print("    Got condition %s for parameter %s." % (condition,self.name))
            pass
        
        
        namespaces=self.get_element_namespaces()
        variables=self.get_xpath_variables(outdoc,inputfilehref)

        if paramdebug:
            print("    Condition xpath variables: %s" % (str(variables)))
            pass
        
        result=outdoc.xpathcontext(element,condition,variables=variables,namespaces=namespaces,noprovenance=True)

        #sys.stderr.write("test_condition: condition=%s variables=%s result=%s\n" % (condition,str({"filename":outdoc.get_filehref().get_bare_unquoted_filename(),"fileurl":outdoc.get_filehref().absurl()}),str(result)))

        if result==True:
            if paramdebug:
                print("    Condition satisfied.")
                pass
            return True
        elif result==False:
            if paramdebug:
                print("    Condition not satisfied.")
                pass
            return False
        elif isinstance(result,numbers.Number):
            if paramdebug:
                print("    Condition evaluated as number %s (%s)." % (str(result),str(result != 0)))
                pass
            return result != 0
        elif isinstance(result,list):
            # got a node-set
            if paramdebug:
                print("    Condition evaluated as node-set of length %d (%s)." % (len(result),str(len(result) != 0)))
                pass
            return len(result) != 0
        else:
            raise ValueError("test_condition: condition \"%s\" returned invalid result (type %s)" % (condition,result.__class__.__name__))
        pass

    def evaluateas(self,typename,outdoc,element,inputfilehref,paramdebug):
        # Check for select= option
        if self.prxdoc.hasattr(self.element,"select"):
            # Select attribute... evaluate xpath in context
            # of element we are operating on

            if paramdebug:
                print("        Parameter %s has \"select\" attribute. Evaluating xpath in output document element context." % (self.name))
                pass
                
            select=self.prxdoc.getattr(self.element,"select")
            
            namespaces=self.get_element_namespaces()
            variables=self.get_xpath_variables(outdoc,inputfilehref)

            selectresult=outdoc.xpathcontext(element,select,variables=variables,namespaces=namespaces)

            if isinstance(selectresult,numbers.Number):
                if paramdebug:
                    print("        XPath evaluation returned a number %s." % (str(selectresult)))
                    pass
                
                return evaluate_from_number(selectresult,typename,self.name)
            elif isinstance(selectresult,list):
                if paramdebug:
                    print("        XPath evaluation returned a node-set of length %d:" % (len(selectresult)))
                    pass
                
                return evaluate_from_elements(outdoc,selectresult,typename,self.name,self.name,paramdebug)
            elif isinstance(selectresult,bool):
                if paramdebug:
                    print("        XPath evaluation returned a boolean %s." % (str(selectresult)))
                    pass
                return evaluate_from_bool(selectresult,typename,self.name,paramdebug)
            elif isinstance(selectresult,basestring):
                if paramdebug:
                    print("        XPath evaluation returned a string \"%s\":" % (str(selectresult)))
                    pass
                return evaluate_from_string(selectresult,typename,self.name,paramdebug)
            else:
                # Some kind of node
                return evaluate_from_elements(outdoc,[selectresult],typename,self.name,self.name,paramdebug)
            pass
        # no select attribute
        return evaluate_from_elements(self.prxdoc,[self.element],typename,self.name,self.name,paramdebug)    
    pass



def evaluate_params(paramdict,name,typename,outdoc,element,inputfilehref,paramdebug):
    params=paramdict[name]
    for param in params:
        if param.test_condition(outdoc,element,inputfilehref,paramdebug):
            return param.evaluateas(typename,outdoc,element,inputfilehref,paramdebug)
        pass
    raise ValueError("No value found for parameter %s for element %s" % (name,etxpath2human(outdoc.get_canonical_etxpath(element),outdoc.nsmap)))

def findparam_concrete(prxnsmap,outdoc,element,arg_nspre,argname,argtype,paramdebug):

    if paramdebug:
        print("    Searching in %s for " % (outdoc.get_filehref().humanurl()),end="")
        if arg_nspre is not None:
            print("%s:%s " % (arg_nspre,argname),end="")
            pass
        else:
            print("%s " % (argname),end="")
            pass
        if argtype is not None:
            print("of type %s " % (argtype))
            pass
        print("starting at %s:" % (dcv.hrefvalue.fromelement(outdoc,element).gethumanfragment()))
        pass
    
    namespaces={}
    namespaces.update(element.nsmap)
    namespaces.update(prxnsmap)
    if None in namespaces:
        del namespaces[None]
        pass

    if arg_nspre is not None:
        useargname="%s:%s" % (arg_nspre,argname)
        if arg_nspre not in namespaces:
            raise NameError("Unknown namespace prefix %s" % (arg_nspre))
        pass
    else:
        useargname=argname
        pass
    children=outdoc.children(element,useargname,namespaces=namespaces)
    return evaluate_from_elements(outdoc,children,argtype,argname,useargname,paramdebug)
    #
    #raise NameError("No child element found")

def findparam(prxnsmap,outdoc,element,argname,paramdebug):
    #     Create a parameter structure for parameter argname from outdoc
    #   element data
    #  ... xpath nsmap should come from outdoc, but updated by prxdoc



    # Argname may be the complete element name
    try: 
        ret=findparam_concrete(prxnsmap,outdoc,element,None,argname,None,paramdebug)
        return ret
        pass
    except NameError:
        pass
    
    if "_" in argname:
        # Argname  may be base_type
        (argnamebase,argnametype)=argname.rsplit("_",1)

        if "_" in argnamebase:
            # Argname may be prefix_base_type
            (argnameprefix,argnamebase_noprefix)=argnamebase.split("_",1)
            try: 
                ret=findparam_concrete(prxnsmap,outdoc,element,argnameprefix,argnamebase_noprefix,argnametype,paramdebug)
                return ret
            except NameError:
                pass
            pass

        # Argname  may be base_type
        try: 
            ret=findparam_concrete(prxnsmap,outdoc,element,None,argnamebase,argnametype,paramdebug)
            return ret
        except NameError:
            pass

        
        # argname maybe prefix_base
        (argnameprefix,argnamebase_noprefix)=argname.split("_",1)
        try: 
            ret=findparam_concrete(prxnsmap,outdoc,element,argnameprefix,argnamebase_noprefix,None,paramdebug)
            return ret
        except NameError:
            pass
        pass
    raise NameError("Element %s: No child element matching \"%s\" found!" % (dcv.hrefvalue.fromelement(outdoc,element).humanurl(),argname))

