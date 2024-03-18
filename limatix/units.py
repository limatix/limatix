import re
import builtins
import numbers

from . import lm_units  # note: main program should call lm_units.units_config("insert_basic_units")
from . import dc_value

HAS_PINT = False
try:
    import pint
    HAS_PINT = True
except ImportError:
    pass


if not hasattr(builtins,"basestring"):
    basestring=str  # python3
    pass


class LimatixUnitManager():
    _registry = None
    _backend = "lm_units"

    def __init__(self) -> None:
        self._registry = self.get_application_registry_pint()
        pass

    @property
    def backend(self):
        return self._backend

    @property
    def registry(self):
        return self._registry.get()

    @property
    def Q(self):
        return self._registry.get().Quantity

    def set_backend(self, backend="lm_units"):
        if (backend == "pint") and not HAS_PINT:
            raise ValueError("pint unit library is not installed")

        if (backend != "pint") and (backend != "lm_units"):
            raise ValueError("invalid backend %s, must be lm_units or pint" % backend)

        self._backend = backend
        pass

    def set_configuration(self, backend, debug=False, **kwargs):
        if debug:
            print("Debug: setting unit configuration for %s backend" % backend)
            print("configuration parameters:")
            for p, v in kwargs.items(): print("%s=%s" % (p, v))

        if backend == "lm_units":
            lm_units.units_config(kwargs.get("configstring", "insert_basic_units"))
        elif backend == "pint":
            if not HAS_PINT:
                print("Warning: trying to specify configuration for pint but it is not installed. configuration parameters will be ignored")
                return
            self.set_application_registry_pint(pint.UnitRegistry(**kwargs))
        else:
            raise NotImplementedError("unit backend %s is unavailable" % backend)
        pass

    def get_application_registry_pint(self):
        return pint.get_application_registry() if HAS_PINT else None

    def set_application_registry_pint(self, registry):
        pint.set_application_registry(registry)
        self._registry = self.get_application_registry_pint()
        pass

    def parse(self, val, units):
        quantity = self.registry.parse_expression("%s %s" % (val, units))

        if units is None:
            matchobj=re.match(R""" *(([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)|([-+]?[iI][nN][fF])|([nN][aA][nN])) *[\[]?([^\]\[]*)[\]]?""",val);
            if matchobj is not None :
                val=float(matchobj.group(1))
                unit=lm_units.parseunits(matchobj.group(8))
                pass
            pass
        else :
            val=float(val)                
            if isinstance(units, basestring):
                unit=lm_units.parseunits(units);
                pass
            else :
                unit=lm_units.copyunits(units);
                pass
            pass

        return val, unit, quantity

    def from_numericunitsvalue(self, val, units=None):
        quantity = self.Q(val.value(), str(val.units()) if val.units() is not None else units)

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

        return val, unit, quantity

    def from_value(self, val, units=None):
        quantity = self.Q(val, str(units) if units is not None else None)

        if units is not None:
            if isinstance(units,basestring):
                unit=lm_units.parseunits(units);
                pass
            else :
                unit=lm_units.copyunits(units);
                pass
            pass

        return val, unit, quantity

    def equal(self, v1, v2):
        if self.backend == "pint":
            if isinstance(v2, dc_value.numericunitsvalue):
                v2 = v2.quantity
            return v1.quantity == v2
        else:
            # print "NumericUnitsValue Eq called!"
            # print self.val==other.value(),self.unit==other.units()
            # print str(self.unit),str(other.units())

            otherval=v2.value()
            otherunit=v2.units()
            
            # print "self.val=%s, otherval=%s" % (str(self.val),str(otherval))
            # print "self.unit=%s, otherunit=%s" % (str(self.unit),str(otherunit))
            unitfactor=lm_units.compareunits(v1.unit,otherunit)
            unitfactor2=lm_units.compareunits(otherunit,v1.unit)
            if unitfactor==0.0 or unitfactor2==0.0:
                # unit mismatch
                return False
            else :
                # avoid roundoff issues by checking strict equality both ways
                if v1.val*unitfactor==otherval or v1.val==otherval*unitfactor2:
                    return True
                else :
                    return False

    def less_than(self, v1, v2):
        if self.backend == "pint":
            if isinstance(v2, dc_value.numericunitsvalue):
                v2 = v2.quantity
            return v1.quantity < v2
        else:
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
        if self.backend == "pint":
            if isinstance(v2, dc_value.numericunitsvalue):
                v2 = v2.quantity
            return v1.quantity <= v2
        else:
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
        if self.backend == "pint":
            if isinstance(v2, dc_value.numericunitsvalue):
                v2 = v2.quantity
            return v1.quantity > v2
        else:
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
        if self.backend == "pint":
            if isinstance(v2, dc_value.numericunitsvalue):
                v2 = v2.quantity
            return v1.quantity >= v2
        else:
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
        if self.backend == "pint":
            v = abs(v.quantity)
            return dc_value.numericunitsvalue(v.m, v.units)
        else:
            return dc_value.numericunitsvalue(abs(v.val), v.unit)

    def round(self, v):
        if self.backend == "pint":
            v = round(v.quantity)
            return dc_value.numericunitsvalue(v.m, v.units)
        else:
            return dc_value.numericunitsvalue(round(v.val), v.unit)

    def power(self, v, p, modulo=None):
        if self.backend == "pint":
            if isinstance(p,dc_value.numericunitsvalue):
                p = p.quantity
                pass

            v = v.quantity**p
            return dc_value.numericunitsvalue(v.m, v.units)
        else:
            if modulo is not None:
                raise ValueError("pow modulo not supported")

            if isinstance(p, dc_value.numericunitsvalue):
                p=p.value("") # need unitless representation of exponent
                pass
            
            return dc_value.numericunitsvalue(v.val**p, lm_units.powerunits(v.unit, p))

        pass
    
    def add(self, v1, v2):
        if self.backend == "pint":
            if isinstance(v2, dc_value.numericunitsvalue):
                v2 = v2.quantity
            v1 = v1.quantity + v2
            return dc_value.numericunitsvalue(v1.m, v1.units)
        else:
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
            
            return dc_value.numericunitsvalue(v1.val + value/unitfactor, v2.unit)

    def subtract(self, v1, v2):
        if self.backend == "pint":
            if isinstance(v2, dc_value.numericunitsvalue):
                v2 = v2.quantity
            v1 = v1.quantity - v2
            return dc_value.numericunitsvalue(v1.m, v1.units)
        else:
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
            
            return dc_value.numericunitsvalue(v1.val - value/unitfactor, v2.unit)
    
    def multiply(self, v1, v2):
        if self.backend == "pint":
            if isinstance(v2, dc_value.numericunitsvalue):
                v2 = v2.quantity
            v1 = v1.quantity * v2
            return dc_value.numericunitsvalue(v1.m, v1.units)
        else:
            if not isinstance(v2, float):
                newunits = lm_units.multiplyunits(v1.unit, v2.units())
                tomul = v2.value()
                pass
            else:
                newunits = v1.unit
                tomul = v2
                pass
            
            return dc_value.numericunitsvalue(v1.val*tomul, newunits)
    
    def divide(self, v1, v2):
        if self.backend == "pint":
            if isinstance(v2, dc_value.numericunitsvalue):
                v2 = v2.quantity
            v1 = v1.quantity / v2
            return dc_value.numericunitsvalue(v1.m, v1.units)
        else:
            if not isinstance(v2,float):
                newunits = lm_units.divideunits(v1.unit, v2.units())
                todiv = v2.value()
                pass
            else:
                newunits = v1.unit
                todiv = v2
                pass

            return dc_value.numericunitsvalue(v1.val/todiv, newunits)

    def true_divide(self, v1, v2):
        if self.backend == "pint":
            if isinstance(v2, dc_value.numericunitsvalue):
                v2 = v2.quantity
            v1 = v1.quantity / v2
            return dc_value.numericunitsvalue(v1.m, v1.units)
        else:
            if not isinstance(v2, float):
                newunits = lm_units.divideunits(v1.unit, v2.units())
                todiv = v2.value()
                pass
            else:
                newunits = v1.unit
                todiv = v2
                pass
            
            return dc_value.numericunitsvalue(v1.val/todiv, newunits);

    def floor_divide(self, v1, v2):
        if self.backend == "pint":
            if isinstance(v2, dc_value.numericunitsvalue):
                v2 = v2.quantity
            v1 = v1.quantity // v2
            return dc_value.numericunitsvalue(v1.m, v1.units)
        else:
            if not isinstance(v2, float):
                newunits = lm_units.divideunits(v1.unit, v2.units())
                todiv = v2.value()
                pass
            else:
                newunits = v1.unit
                todiv = v2
                pass

            return dc_value.numericunitsvalue(v1.val//todiv, newunits);

    pass

manager = LimatixUnitManager()
