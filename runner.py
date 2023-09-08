from t_types import *
import prsr, lexer

project_path = ""

modules = {

}

class DynamicValue:
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return "asDynmc(" + str(self.value) + ")"

def toPyVar(t):
    if type(t["value"]) == list:
        return list(toPyVar(i) for i in t["value"])
    else:
        return t["value"]

class PyFunc:
    def __init__(self, func):
        self.func = func
    
    def execute(self, parameters):
        parameters = toPyVar(parameters)
        return self.func(*parameters)

class Func:
    def __init__(self, vars, params, body):
        self.fp = params
        self.fb = body
        self.body = body["value"]
        self.r = Runner(self.body)
        self.r.var_list = DynamicValue({"this": vars})
        self.params = params["value"]

    def execute(self, params:dict):
        for i in range(len(self.params)):
            self.r.var_list.value[self.params[i]["value"][0]] = DynamicValue(params["value"][i])
        return self.r.run()
    
    def new(self, vars):
        return Func(vars, self.fp, self.fb)

def imp(file:str):
    lib_name = file.replace('.py', '')
    if lib_name in modules: return modules[lib_name]
    if file.endswith(".py"):
        exec(f"from libs.{lib_name} import funcs as {lib_name + 'fcodelib'}")
        funcs = eval(lib_name + 'fcodelib')
        if type(funcs) == dict:
            fk = list(funcs.keys())
            f = DynamicValue({})
            for i in range(len(funcs)):
                f.value[fk[i]] = DynamicValue(PyFunc(funcs[fk[i]]))
            modules[lib_name] = f
            return f
        else:
            modules[lib_name] = DynamicValue(funcs)
            return funcs
    elif file.endswith(".fcode"):
        f = open(project_path + "/" + file)
        lib = Runner(prsr.Parser(lexer.Lexer(f.read().replace("\n", " ")).lex()).expression())
        lib.run()
        modules[lib_name] = lib.var_list
        return modules[lib_name]

def new(cls: dict):
    vls = list(cls.values())
    nl = DynamicValue({})
    for i in range(len(vls)):
        if type(vls[i].value) in [dict, PyFunc]:
            nl.value[list(cls.keys())[i]] = DynamicValue(vls[i].value)
        else:
            nl.value[list(cls.keys())[i]] = DynamicValue(vls[i].value.new(nl))
    return nl

class Runner:
    def __init__(self, ast):
        self.ast = ast
        self.var_list = DynamicValue({})

    def run_node(self, node):
        if node["type"] in [INT, FLT, STR, BOL, LST]:
            return node
        
        elif node["type"] == "+":
            left = self.run_node(node["left"])
            right = self.run_node(node["right"])
            return {"type": left["type"], "value": left["value"] + right["value"]}
        elif node["type"] == "-":
            left = self.run_node(node["left"])
            right = self.run_node(node["right"])
            return {"type": left["type"], "value": left["value"] - right["value"]}
        elif node["type"] == "*":
            left = self.run_node(node["left"])
            right = self.run_node(node["right"])
            return {"type": left["type"], "value": left["value"] * right["value"]}
        elif node["type"] == "/":
            left = self.run_node(node["left"])
            right = self.run_node(node["right"])
            return {"type": left["type"], "value": left["value"] / right["value"]}
        elif node["type"] == "%":
            left = self.run_node(node["left"])
            right = self.run_node(node["right"])
            return {"type": left["type"], "value": left["value"] % right["value"]}
        
        elif node["type"] == "<":
            left = self.run_node(node["left"])
            right = self.run_node(node["right"])
            return {"type": BOL, "value": left["value"] < right["value"]}
        elif node["type"] == ">":
            left = self.run_node(node["left"])
            right = self.run_node(node["right"])
            return {"type": BOL, "value": left["value"] > right["value"]}
        
        elif node["type"] == "and":
            left = self.run_node(node["left"])
            right = self.run_node(node["right"])
            return {"type": BOL, "value": left["value"] and right["value"]}
        elif node["type"] == "or":
            left = self.run_node(node["left"])
            right = self.run_node(node["right"])
            return {"type": BOL, "value": left["value"] or right["value"]}
        
        
        elif node["type"] == "is":
            left = self.run_node(node["left"])
            right = self.run_node(node["right"])
            return {"type": BOL, "value": left["value"] is right["value"]}
        elif node["type"] == "isnot":
            left = self.run_node(node["left"])
            right = self.run_node(node["right"])
            return {"type": BOL, "value": left["value"] is not right["value"]}

        elif node["type"] == IDN:
            t = self.var_list
            for i in node["value"]:
                t = t.value[i]
            return t.value if type(t) == DynamicValue else t
        
        elif node["type"] == "vardef":
            v = self.var_list
            for k in node["name"]["value"]:
                if k not in v.value:
                    v.value[k] = DynamicValue({})
                v = v.value[k]
            val = self.run_node(node["value"])
            if type(val) == DynamicValue: val = val.value
            v.value = val
        elif node["type"] == "funcdef":
            v = self.var_list
            for k in node["name"]["value"]:
                if k not in v.value:
                    v.value[k] = DynamicValue({})
                v = v.value[k]
            v.value = Func(self.var_list, node["param"], node["body"])

        elif node["type"] == "delete":
            v = self.var_list
            for k in node["var"]["value"][0:len(node["var"]["value"]) - 1]:
                if k not in v.value:
                    v.value[k] = DynamicValue({})
                v = v.value[k]
            del v.value[node["var"]["value"][len(node["var"]["value"]) - 1]]

        elif node["type"] == "import":
            mn = self.run_node(node["module"])["value"]
            self.var_list.value[mn.replace(".py", "").replace(".fcode", "")] = imp(mn)
        
        elif node["type"] == "return":
            return self.run_node(node["value"])

        elif node["type"] == "funccall":
            fn = self.run_node(node["name"])
            if type(fn) in [Func, PyFunc]:
                ret = fn.execute({"type": PRM, "value": list(self.run_node(i) for i in node["param"]["value"])})
                if type(fn) == PyFunc:
                    if ret in [True, False]: return {"type": BOL, "value": ret}
                    else: return lexer.Lexer(f"\"{repr(ret)[1:len(repr(ret)) - 1]}\"" if type(repr(ret)) == str else repr(ret)).lex()[0]
                else:
                    return ret
            else:
                nl = new(fn)
                nl.value["constructor"].value.execute({"type": PRM, "value": list(self.run_node(i) for i in node["param"]["value"])})
                return nl

    def run(self):
        for a in self.ast:
            self.run_node(a)
            