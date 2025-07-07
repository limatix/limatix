import re
import builtins
import numbers
import math
import copy
from urllib.parse import quote

from . import lm_units  # note: main program should call lm_units.units_config("insert_basic_units")
#from . import dc_value




if not hasattr(builtins,"basestring"):
    basestring=str  # python3
    pass

class LimatixUnitImplementation():
    _backend = None
    _initialized = None
    dcv = None
    
    def __init__(self) -> None:

        from . import dc_value as dcv
        self.dcv = dcv
        self._initialized = False
        pass

    @property
    def backend(self):
        return self._backend


class LM_UnitsImplementation(LimatixUnitImplementation):
    _backend = None
    _initialized = None
    
    def __init__(self, debug=False,filename_context_href = None, **kwargs) -> None:
        super().__init__()
        self._backend = "lm_units"

        if debug:
            print("Debug: setting unit configuration for lm_units backend")
            print("configuration parameters:")
            for p, v in kwargs.items(): print("%s=%s" % (p, v))
            pass
        
        lm_units.units_config(kwargs.get("configstring", "insert_basic_units"))
        self._initialized=True
        pass
    
    def value_in_units(self,v,units):
        if units is None:
            return v.val;
        
        if isinstance(units,basestring):
            unitstruct=self.parseunits(units)
            pass
        else :
            unitstruct=units
            pass
        
        # print type(self.unit)
        # print type(units)
        # print type(units) is str
        # print type(self.unit)
        unitfactor=lm_units.compareunits(v.unit,unitstruct)
        # print unitfactor
        if unitfactor==0.0:
            raise ValueError("Incompatible units: %s and %s" % (str(v.unit),str(unitstruct)))
        
        return v.val*unitfactor

    def convert_units_to(self,v,unit):
        return type(v)(self.value_in_units(v,unit),unit)
    
    def units(self,v):
        
        return lm_units.copyunits(v.unit)
    
    def get_application_registry_pint(self):
        return None

    def parseunits(self,u):
        if u is None:
            return None
        return lm_units.parseunits(u)

    def parse(self, val, units, defunits,parse_complex=False):
        assert(self._initialized)

        goal_type=float
        match_pattern=R""" *(([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)|([-+]?[iI][nN][fF])|([nN][aA][nN])) *[\[]?([^\]\[]*)[\]]?"""
        if parse_complex:
            goal_type=complex
            match_pattern=R""" *([\(]? *([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?) *[+-] *([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?[ij]?) *?[\)]?) *[\[]?([^\]\[]*)[\]]?"""
            pass
        
        if units is None:
            matchobj=re.match(match_pattern,val);
            if matchobj is not None :
                val=goal_type(matchobj.group(1))
                unit=lm_units.parseunits(matchobj.group(8))
                pass
            else:
                if defunits is not None:
                    defunit = lm_units.parseunits(defunits)
                    unit = defunit
                    pass
                pass
            if unit is None:
                unit = lm_units.createunits()
                pass
            pass
        else :
            val=goal_type(val)                
            if isinstance(units, basestring):
                unit=lm_units.parseunits(units);
                pass
            else :
                unit=lm_units.copyunits(units);
                pass
            pass

        return (val, unit)

    def from_numericunitsvalue(self, val, units=None):
        assert(self._initialized)

        # val is already a dc_value object
        if units is None:
            val=val.value()
            unit=val.units()
            pass
        else : 
            if isinstance(units,basestring):
                unitstruct=lm_units.parseunits(units)
                pass
            else: 
                unitstruct=units
                pass
            
            val=val.value(unitstruct)
            unit=lm_units.copyunits(unitstruct)
            pass

        return (val, unit)

    def from_value(self, val, units=None, defunit=None): #defunit already parsed
        assert(self._initialized)

        if units is not None:
            if isinstance(units,basestring):
                unit=lm_units.parseunits(units);
                pass
            else :
                unit=lm_units.copyunits(units);
                pass
            pass
        else:
            if defunit is None:
                unit = lm_units.parseunits("unitless")
                pass
            else:
                unit = copy.deepcopy(defunit)
                pass
            pass
                
        if val is None:
            val = math.nan
            pass
        return (val, unit)

    
    def format(self,v):
       
       

      
        return "%s %s" % (repr(v.value(v.unit)),str(v.unit))
    def value_from_quantity(self,v):
        return v[0]

    def units_from_quantity(self,v):
        return v[1]

    def simplifyunits(self,v):
        unitcopy=lm_units.copyunits(v.unit)
        lm_units.simplifyunits(unitcopy)
        coefficient=lm_units.extractcoefficient(unitcopy);

        return type(v)(v.val*coefficient,unitcopy)
    
    def isnan(self,v):
        return math.isnan(v.val)
    
    def equal(self, v1, v2):
        assert(self._initialized)
      
        # print "NumericUnitsValue Eq called!"
        # print self.val==other.value(),self.unit==other.units()
        # print str(self.unit),str(other.units())

        (ourval,ourunit)=v1.quantity
        if isinstance(v2,self.dcv.numericunitsvalue) or isinstance(v2,self.dcv.complexunitsvalue):
            (otherval,otherunit)=v2.quantity
            pass
        else:
            otherval = v2
            otherunit = lm_units.createunits()
            pass
        
        # print "self.val=%s, otherval=%s" % (str(self.val),str(otherval))
        # print "self.unit=%s, otherunit=%s" % (str(self.unit),str(otherunit))
        unitfactor=lm_units.compareunits(ourunit,otherunit)
        unitfactor2=lm_units.compareunits(otherunit,ourunit)
        if unitfactor==0.0 or unitfactor2==0.0:
            # unit mismatch
            return False
        else :
            # avoid roundoff issues by checking strict equality both ways
            if v1.val*unitfactor==otherval or v1.val==otherval*unitfactor2:
                return True
            pass

        return False

    def equiv(self, v1, v2): #like equal, but nan is equivalent to NaN
        assert(self._initialized)
      
        # print "NumericUnitsValue Eq called!"
        # print self.val==other.value(),self.unit==other.units()
        # print str(self.unit),str(other.units())
        
        (ourval,ourunit)=v1.quantity
        if isinstance(v2,self.dcv.numericunitsvalue) or isinstance(v2,self.dcv.complexunitsvalue):
            (otherval,otherunit)=v2.quantity
            pass
        else:
            otherval = v2
            otherunit = lm_units.createunits()
            pass
        
        # print "self.val=%s, otherval=%s" % (str(self.val),str(otherval))
        # print "self.unit=%s, otherunit=%s" % (str(self.unit),str(otherunit))
        unitfactor=lm_units.compareunits(ourunit,otherunit)
        unitfactor2=lm_units.compareunits(otherunit,ourunit)
        if unitfactor==0.0 or unitfactor2==0.0:
            # unit mismatch
            return False
        else :
            if math.isnan(v1.val) and math.isnan(otherval):
                return True #nan equivalence
            # avoid roundoff issues by checking strict equality both ways
            if v1.val*unitfactor==otherval or v1.val==otherval*unitfactor2:
                return True
            pass

        return False


    def less_than(self, v1, v2):
        assert(self._initialized)
       
        if isinstance(v2,numbers.Number):
            unitfactor = lm_units.compareunits(v1.unit, lm_units.createunits())            
            value = v2
            pass        
        else:
            unitfactor = lm_units.compareunits(v1.unit, v2.units())
            value = v2.value()
            pass
        if unitfactor == 0.0:
            raise ValueError("Attempting to add values with incompatible units %s and %s" % (str(v1.unit), str(v2.units())))
        
        return v1.val < (value / unitfactor)

    def less_than_equal(self, v1, v2):
        assert(self._initialized)
       
        if isinstance(v2, numbers.Number):
            unitfactor=lm_units.compareunits(v1.unit, lm_units.createunits())            
            value=v2
            pass        
        else:
            unitfactor=lm_units.compareunits(v1.unit, v2.units())
            value=v2.value()
            pass
        if unitfactor == 0.0:
            raise ValueError("Attempting to add values with incompatible units %s and %s" % (str(v1.unit), str(v2.units())))
        
        return v1.val <= (value / unitfactor)

    def greater_than(self, v1, v2):
        assert(self._initialized)
      
        if isinstance(v2,numbers.Number):
            unitfactor=lm_units.compareunits(v1.unit, lm_units.createunits())            
            value=v2
            pass        
        else:
            unitfactor=lm_units.compareunits(v1.unit, v2.units())
            value=v2.value()
            pass
        if unitfactor == 0.0:
            raise ValueError("Attempting to add values with incompatible units %s and %s" % (str(v1.unit), str(v2.units())))
            
        return v1.val > (value / unitfactor)

    def greater_than_equal(self, v1, v2):
        assert(self._initialized)
       
        if isinstance(v2, numbers.Number):
            unitfactor = lm_units.compareunits(v1.unit, lm_units.createunits())            
            value=v2
            pass        
        else:
            unitfactor = lm_units.compareunits(v1.unit, v2.units())
            value = v2.value()
            pass
        if unitfactor == 0.0:
            raise ValueError("Attempting to add values with incompatible units %s and %s" % (str(v1.unit), str(v2.units())))
            
        return v1.val >= (value / unitfactor)

    def absolute_value(self, v):
        assert(self._initialized)
        return type(v)(abs(v.val), v.unit)

    def round(self, v):
        assert(self._initialized)
        return type(v)(round(v.val), v.unit)

    def power(self, v, p, modulo=None):
        assert(self._initialized)
    
        if modulo is not None:
            raise ValueError("pow modulo not supported")

        if isinstance(p, type(v)):
            p=p.value("") # need unitless representation of exponent
            pass
            
        return type(v)(v.val**p, lm_units.powerunits(v.unit, p))

    
    def add(self, v1, v2):
        assert(self._initialized)
    
        if isinstance(v2, numbers.Number):
            unitfactor = lm_units.compareunits(v1.unit, lm_units.createunits())            
            value = v2
            pass        
        else:
            unitfactor = lm_units.compareunits(v1.unit, v2.units())
            value = v2.value()
            pass
        if unitfactor == 0.0:
            raise ValueError("Attempting to add values with incompatible units %s and %s" % (str(v1.unit), str(v2.units())))
            
        return type(v1)(v1.val + value/unitfactor, v2.unit)

    def subtract(self, v1, v2):
        assert(self._initialized)
        
        if isinstance(v2, numbers.Number):
            unitfactor = lm_units.compareunits(v1.unit, lm_units.createunits())
            value = v2
            pass        
        else:
            unitfactor = lm_units.compareunits(v1.unit, v2.units())
            value = v2.value()
            pass
            
        if unitfactor == 0.0:
            raise ValueError("Attempting to add values with incompatible units %s and %s" % (str(v1.unit), str(v2.units())))
            
        return type(v1)(v1.val - value/unitfactor, v2.unit)
    
    def multiply(self, v1, v2):
        assert(self._initialized)
    
        if not isinstance(v2, numbers.Number):
            newunits = lm_units.multiplyunits(v1.unit, v2.units())
            tomul = v2.value()
            pass
        else:
            newunits = v1.unit
            tomul = v2
            pass
            
        return type(v1)(v1.val*tomul, newunits)
    
    def divide(self, v1, v2):
        assert(self._initialized)
     
        if not isinstance(v2,numbers.Number):
            newunits = lm_units.divideunits(v1.unit, v2.units())
            todiv = v2.value()
            pass
        else:
            newunits = v1.unit
            todiv = v2
            pass

        return type(v1)(v1.val/todiv, newunits)

    def true_divide(self, v1, v2):
        assert(self._initialized)
        if not isinstance(v2, numbers.Number):
            newunits = lm_units.divideunits(v1.unit, v2.units())
            todiv = v2.value()
            pass
        else:
            newunits = v1.unit
            todiv = v2
            pass
            
        return type(v1)(v1.val/todiv, newunits);

    def floor_divide(self, v1, v2):
        assert(self._initialized)
        if not isinstance(v2, numbers.Number):
            newunits = lm_units.divideunits(v1.unit, v2.units())
            todiv = v2.value()
            pass
        else:
            newunits = v1.unit
            todiv = v2
            pass

        return type(v1)(v1.val//todiv, newunits);
    pass
    

class PintUnitImplementation(LimatixUnitImplementation):
    _registry = None
    _backend = None
    _initialized = None

    #these properties are probably unnecessary and slowing things down compared to storing member variables directly
    @property
    def registry(self):
        return self._registry

    @property
    def Q(self):
        return self._registry.Quantity
    
    def __init__(self, debug=False,filename_context_href = None, **kwargs) -> None:
        super().__init__()
        self._backend = "pint"
    
        try:
            import pint
            pass
        except ImportError:
            raise ValueError("pint unit library is not installed")
        
        if debug:
            print("Debug: setting unit configuration for pint backend")
            print("configuration parameters:")
            for p, v in kwargs.items(): print("%s=%s" % (p, v))
            pass
        
        if len(kwargs) > 0:
            if filename_context_href is not None:
                #Update file name and cache folder args, adding context
                
                kwargs = { arg: self.dcv.hrefvalue(quote(kwargs[arg]),contexthref = filename_context_href).getpath() if arg == "filename" or arg == "cache_folder" else kwargs[arg] for arg in kwargs }
                pass
            self._registry = pint.UnitRegistry(**kwargs)
            pint.set_application_registry(self._registry)
            pass
        else:
            self._registry = pint.get_application_registry()
            pass
        self._initialized=True
        pass

    def value_in_units(self,v,units):
        return v.quantity.to(units).m

    def convert_units_to(self,v,units):
        return type(v)(v.quantity.to(units),units)
    
    def units(self,v):
        return v.quantity.units

    def format(self,v):
        return str(v.quantity)

    def get_application_registry_pint(self):
        import pint
        return pint.get_application_registry()

    def parseunits(self,u):
        if u is None:
            return None
        return self.Q(u)
    
    def parse(self, val, units, defunits,parse_complex=False):
        assert(self._initialized)
        if units is None:
            units=defunits
            pass
        if parse_complex:
            if isinstance(val,str):
                val_split = val.split()
                if len(val_split) > 1:
                    quantity = complex(val_split[0])*self.registry.parse_expression(val_split[1:])
                    pass
                else:
                    quantity = complex(val)
                    pass
                pass
            if not hasattr(quantity,"units"):
                quantity = quantity*self.registry.parse_expression(units)
                pass
            pass
        else:
        
            quantity = self.registry.parse_expression(val)
            if not hasattr(quantity,"units"):
                quantity = quantity*self.registry.parse_expression(units)
                pass
            pass
            
      

        return quantity

    def from_numericunitsvalue(self, val, units=None):
        assert(self._initialized)
        if units is None:
            return self.Q(val.quantity)

        return self.Q(val.quantity).to(units)
     

    def from_value(self, val, units=None,defunit=None): #defunit already parsed
        assert(self._initialized)
        if val is None:
            val = math.nan
            pass
        if units is not None:
            quantity = self.Q(val,str(units))
            pass
        else:
            if not hasattr(val,"units") and defunit is not None:
                quantity = val*defunit
                pass
            else:
                quantity = self.Q(val,None)
                pass
            pass
        return quantity

    def value_from_quantity(self,q):
        return q.m

    def units_from_quantity(self,q):
        return q.units

    def simplifyunits(self,v):
        return type(v)(v.quantity.to_compact())
    
    def isnan(self,v):
        return math.isnan(v.quantity.m)
    
    def equal(self, v1, v2):
        assert(self._initialized)
        if isinstance(v2, self.dcv.numericunitsvalue) or isinstance(v2, self.dcv.complexunitsvalue):
            v2 = v2.quantity
            pass
        return v1.quantity == v2
    
    def equiv(self, v1, v2): #like equal, but nan's count as matching
        assert(self._initialized)
        if isinstance(v2, self.dcv.numericunitsvalue) or isinstance(v2, self.dcv.complexunitsvalue):
            v2 = v2.quantity
            pass
        if math.isnan(v1.quantity.m) and math.isnan(v2.quantity.m):
            return True
        
        return v1.quantity == v2


    def less_than(self, v1, v2):
        assert(self._initialized)
        if isinstance(v2, type(v1)):
            v2 = v2.quantity
            pass
        return v1.quantity < v2
       
    def less_than_equal(self, v1, v2):
        assert(self._initialized)
       
        if isinstance(v2, type(v1)):
            v2 = v2.quantity
            pass
        
        return v1.quantity <= v2

         
    def greater_than(self, v1, v2):
        assert(self._initialized)
        if isinstance(v2, type(v1)):
            v2 = v2.quantity
            pass
        return v1.quantity > v2

    def greater_than_equal(self, v1, v2):
        assert(self._initialized)
        if isinstance(v2, type(v1)):
            v2 = v2.quantity
            pass
        return v1.quantity >= v2

    def absolute_value(self, v):
        assert(self._initialized)
        v_abs = abs(v.quantity)
        return type(v)(v_abs.m, v_abs.units)

    def round(self, v):
        assert(self._initialized)
        v_rnd = round(v.quantity)
        return type(v)(v_rnd.m, v_rnd.units)

    def power(self, v, p, modulo=None):
        assert(self._initialized)
        if isinstance(p,type(v)):
            p = p.quantity
            pass

        v_pow = v.quantity**p
        return type(v)(v_pow.m, v_pow.units)
    
    
    def add(self, v1, v2):
        assert(self._initialized)
        if isinstance(v2, self.dcv.numericunitsvalue) or isinstance(v2,self.dcv.complexunitsvalue):
            v2 = v2.quantity
            pass
        v1_sum = v1.quantity + v2
        return type(v1)(v1_sum.m, v1_sum.units)

    def subtract(self, v1, v2):
        assert(self._initialized)
        if isinstance(v2, self.dcv.numericunitsvalue) or isinstance(v2,self.dcv.complexunitsvalue):
            v2 = v2.quantity
            pass
        v1_diff = v1.quantity - v2
        return type(v1)(v1_diff.m, v1_diff.units)
            
    
    def multiply(self, v1, v2):
        assert(self._initialized)
        if isinstance(v2, self.dcv.numericunitsvalue) or isinstance(v2,self.dcv.complexunitsvalue):
            v2 = v2.quantity
            pass
        v1_prod = v1.quantity * v2
        return type(v1)(v1_prod.m, v1_prod.units)
   
    def divide(self, v1, v2):
        assert(self._initialized)
        if isinstance(v2, self.dcv.numericunitsvalue) or isinstance(v2,self.dcv.complexunitsvalue):
            v2 = v2.quantity
            pass
        v1_quot = v1.quantity / v2
        return type(v1)(v1_quot.m, v1_quot.units)
       
    def true_divide(self, v1, v2):
        assert(self._initialized)
        if isinstance(v2, self.dcv.numericunitsvalue) or isinstance(v2,self.dcv.complexunitsvalue):
            v2 = v2.quantity
            pass
        v1_quot = v1.quantity / v2
        return type(v1)(v1_quot.m, v1_quot.units)
      
    def floor_divide(self, v1, v2):
        assert(self._initialized)
        if isinstance(v2, self.dcv.numericunitsvalue) or isinstance(v2,self.dcv.complexunitsvalue):
            v2 = v2.quantity
            pass
        v1_quot = v1.quantity // v2
        return type(v1)(v1_quot.m, v1_quot.units)
      
    pass


manager = None

def configure_units(unit_engine,debug = False,filename_context_href = None,**kwargs):
    global manager
    if manager is not None:
        raise ValueError("configure_units has already been run!")

    if unit_engine == "pint":
        manager = PintUnitImplementation(debug=debug,filename_context_href = filename_context_href,**kwargs)
        pass
    elif unit_engine == "lm_units":
        manager=LM_UnitsImplementation(debug=debug,filename_context_href = filename_context_href,**kwargs)
   
        pass

    pass
