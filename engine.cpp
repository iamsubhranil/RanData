#include "engine.h"

#include "display.h"

#define CALL_FUNCTION(func) ((this)->*func)

int Engine::argumentCounts[] = {
#define KEYWORD(x, y, z) z,
#include "keywords.h"
};

Engine::ExpressionRule Engine::expressionRules[] = {

    NULL, // TOKEN_LEFT_PAREN,
    NULL, // TOKEN_RIGHT_PAREN,

    NULL, // TOKEN_EQUAL,
    NULL, // TOKEN_COMMA,

    &Engine::identifierExpression, // TOKEN_IDENTIFIER,
    &Engine::stringExpression,     // TOKEN_STRING,
    &Engine::numberExpression,     // TOKEN_NUMBER,

#define KEYWORD(x, y, z) &Engine::functionExpression,
#include "keywords.h"

    NULL, // TOKEN_ERROR,
    NULL, // TOKEN_EOF
};

Token Engine::consume(TokenType t, const char *message) {
	Token tok = scanner.scanNextToken();
	if(tok.type != t) {
		throw EngineException(tok, message);
	}
	return tok;
}

// parser

Expression Engine::identifierExpression(Token iden) {
	return Expression(iden, Value::identifier(String::from(iden, true)));
}

Expression Engine::stringExpression(Token str) {
	return Expression(str, Value(String::from(str.start + 1, str.length - 2)));
}

Expression Engine::numberExpression(Token num) {
	char *end;
	long  n = strtol(num.start, &end, 10);
	if(end != num.start + num.length) {
		throw EngineException(num, "Invalid numeric value!");
	}
	return Expression(num, Value(n));
}

Expression Engine::parseExpression(Token t) {
	ExpressionRule er = expressionRules[t.type];
	if(er == NULL) {
		throw EngineException(t, "Expected argument!");
	}
	return CALL_FUNCTION(er)(t);
}

Expression Engine::parseExpression() {
	return parseExpression(scanner.scanNextToken());
}

Expression Engine::functionExpression(Token a) {
	if(a.type == TOKEN_print) {
		throw EngineException(a, "print() cannot be assigned to a rule!");
	}
	consume(TOKEN_LEFT_PAREN, "Expected '(' after function call!");
	FunctionCall f    = FunctionCall::from(a.type);
	int          args = argumentCounts[a.type - TOKEN_append];
	// there should be at least one argument
	Expression fa = parseExpression();
	if(args != -1) {
		f.args    = (Expression *)malloc(sizeof(Expression) * args);
		f.args[0] = fa;
		int i     = 1;
		while(--args) {
			consume(TOKEN_COMMA, "Expected ',' after argument!");
			f.args[i++] = parseExpression();
		}
		f.count = i;
		consume(TOKEN_RIGHT_PAREN, "Expected ')' after function call!");
	} else {
		f.args    = (Expression *)malloc(sizeof(Expression));
		f.args[0] = fa;
		int   i   = 1;
		Token arg;
		while((arg = scanner.scanNextToken()).type != TOKEN_RIGHT_PAREN) {
			if(arg.type != TOKEN_COMMA) {
				throw EngineException(arg, "Expected ',' after argument!");
			}
			f.args =
			    (Expression *)realloc(f.args, sizeof(Expression) * (i + 1));
			f.args[i++] = parseExpression();
		}
		f.count = i;
	}
	return Expression(a, f);
}

// execution

Result Engine::numberExecute(Expression num, int times) {
	return Result(Value(Repeat::from(num.as.literal, times)), true);
}

Result Engine::stringExecute(Expression str, int times) {
	return Result(Value(Repeat::from(str.as.literal, times)), true);
}

Result Engine::identifierExecute(Expression id, int times) {
	Value iden = id.as.literal;
	if(results.contains(iden.as.str)) {
		return results[iden.as.str];
	} else if(!rules.contains(iden.as.str)) {
		throw EngineException("No such rule found!");
	}
	Expression repr = rules[iden.as.str];
	Result     res  = evaluateExpression(repr, times);
	// cache the result
	results[iden.as.str] = res;
	return res;
}

// primitive functions
// args: a 2D array, where each row contains arguments for iteration i
//                         each column contains the jth argument
// count: total number of arguments passed to the function
// isConstant: denotes whether the arguments are constant, i.e. is the
//              same vertically
// times: number of iterations

String *appendOneRow(Result *args, int count, int row) {
	String *strings[count];
	// calculate the total size
	int totalSize = 0;
	for(int i = 0; i < count; i++) {
		strings[i] = String::toString(Engine::getAt(args[i].val, row));
		totalSize += strings[i]->size;
	}
	// allocate the whole string at once
	String *res =
	    (String *)malloc(sizeof(String) + (sizeof(char) * (totalSize + 1)));
	res->size  = totalSize;
	int oldidx = 0;
	// copy the rest
	for(int i = 0; i < count; i++) {
		memcpy(&(res->values()[oldidx]), strings[i]->values(),
		       strings[i]->size);
		oldidx += strings[i]->size;
	}
	res->values()[totalSize] = 0;
	return res;
}

Result Engine::appendExecute(Token t, Result *args, int count, bool isConstant,
                             int times) {
	(void)t;
	if(isConstant) {
		return Result(Repeat::from(Value(appendOneRow(args, count, 0)), times));
	} else {
		// all arguments are either array, or repeat,
		// or string, or number
		// the result will be an array of array,
		// where each subarray will contain the
		// append of each row collection of arguments
		Array *res = Array::create(times);
		for(int i = 0; i < times; i++) {
			res->at(i) = Value(appendOneRow(args, count, i));
		}
		return Result(Value(res));
	}
}

Result Engine::lowerExecute(Token t, Result *args, int count, bool isConstant,
                            int times) {
	(void)count;
	(void)t;
	if(isConstant) {
		return Result(Repeat::from(
		    String::toString(getAt(args[0].val, 0), true)->lower(), times));
	} else {
		Array *res = Array::create(times);
		for(int i = 0; i < times; i++) {
			res->at(i) =
			    Value(String::toString(getAt(args[0].val, i), true)->lower());
		}
		return Result(Value(res));
	}
}

Result Engine::number_betweenExecute(Token t, Result *args, int count,
                                     bool isConstant, int times) {
	(void)count;
	if(isConstant) {
		if(!validateType(args[0].val, Value::Number) ||
		   !validateType(args[1].val, Value::Number)) {
			throw EngineException(t, "Both arguments of 'number_between' "
			                         "must be valid numbers!");
		}
		Array *res = Array::create(times);
		random.setIntGenerateRange(args[0].val.as.number,
		                           args[1].val.as.number);
		for(int i = 0; i < times; i++) {
			res->at(i) = Value(random.nextIntInRange());
		}
		return Result(Value(res));
	} else {
		Array *res = Array::create(times);
		for(int i = 0; i < times; i++) {
			Value v1 = getAt(args[0].val, i);
			Value v2 = getAt(args[1].val, i);
			if(!validateType(v1, Value::Number) ||
			   !validateType(v2, Value::Number)) {
				throw EngineException(
				    t, "Both arguments of 'number_between' must be valid "
				       "numbers!");
			}
			random.setIntGenerateRange(v1.as.number, v2.as.number);
			res->at(i) = Value(random.nextIntInRange());
		}
		return Result(Value(res));
	}
}

Result Engine::number_uptoExecute(Token t, Result *args, int count,
                                  bool isConstant, int times) {
	(void)count;
	if(isConstant) {
		if(!validateType(args[0].val, Value::Number)) {
			throw EngineException(
			    t, "Argument of 'number_upto' must be a valid number!");
		}
		Array *res = Array::create(times);
		random.setIntGenerateRange(0, getAt(args[0].val, 0).as.number);
		for(int i = 0; i < times; i++) {
			res->at(i) = Value(random.nextIntInRange());
		}
		return Result(Value(res));
	} else {
		Array *res = Array::create(times);
		for(int i = 0; i < times; i++) {
			Value v1 = getAt(args[0].val, i);
			if(!validateType(v1, Value::Number)) {
				throw EngineException(
				    t, "Argument of 'number_upto' must be a valid "
				       "number!");
			}
			random.setIntGenerateRange(0, v1.as.number);
			res->at(i) = Value(random.nextIntInRange());
		}
		return Result(Value(res));
	}
}

Result Engine::one_ofExecute(Token t, Result *args, int count, bool isConstant,
                             int times) {
	(void)t;
	if(isConstant) {
		Array *res = Array::create(times);
		random.setIntGenerateRange(0, count - 1);
		for(int i = 0; i < times; i++) {
			res->at(i) = getAt(args[random.nextIntInRange()].val, 0);
		}
		return Result(Value(res));
	} else {
		Array *res = Array::create(times);
		random.setIntGenerateRange(0, count - 1);
		for(int i = 0; i < times; i++) {
			res->at(i) = getAt(args[random.nextIntInRange()].val, i);
		}
		return Result(Value(res));
	}
	return Result(Value());
}

Result Engine::one_of_uniqueExecute(Token t, Result *args, int count,
                                    bool isConstant, int times) {
	(void)t;
	(void)args;
	(void)count;
	(void)isConstant;
	(void)times;
	return Result(Value());
}

Result Engine::printExecute(Token t, Result *args, int count, bool isConstant,
                            int times) {
	(void)t;
	(void)args;
	(void)count;
	(void)isConstant;
	(void)times;
	return Result(Value());
}

Result Engine::functionExecute(Expression e, int times) {
	Result *results =
	    (Result *)malloc(sizeof(Result) * e.as.functionCall.count);
	bool isConstant = true;
	for(int i = 0; i < e.as.functionCall.count; i++) {
		results[i] = evaluateExpression(e.as.functionCall.args[i], times);
		isConstant = isConstant & results[i].isConstant;
	}
	switch(e.as.functionCall.name) {
#define KEYWORD(x, y, z)                                             \
	case TOKEN_##x:                                                  \
		return x##Execute(e.token, results, e.as.functionCall.count, \
		                  isConstant, times);
#include "keywords.h"
		default:
			panic("Invalid function type '%d' passed for execution!",
			      e.as.functionCall.name);
	}
}

Result Engine::evaluateExpression(Expression e, int times) {
	switch(e.type) {
		case Expression::FunctionCall: return functionExecute(e, times);
		case Expression::Literal: {
			Value v = e.as.literal;
			switch(v.type) {
				case Value::Number: return numberExecute(e, times);
				case Value::String: return stringExecute(e, times);
				case Value::Identifier: return identifierExecute(e, times);
				default:
					panic("Invalid value type '%d' passed for execution!",
					      v.type);
			}
		}
	}
}

Value Engine::getAt(Value v, int idx) {
	switch(v.type) {
		case Value::String:
		case Value::Identifier:
		case Value::Number: return v;
		case Value::Repeat: return v.as.rep->val;
		case Value::Array: return v.as.arr->at(idx);
		default: panic("Invalid getAt on '%s'!", Value::TypeStrings[v.type]);
	}
}

bool Engine::validateType(Value arg, Value::Type type) {
	if(arg.type == type)
		return true;
	switch(arg.type) {
		case Value::Repeat: return validateType(arg.as.rep->val, type);
		case Value::Array:
			for(int i = 0; i < arg.as.arr->size; i++) {
				if(!validateType(arg.as.arr->at(i), type))
					return false;
			}
		default: return false;
	}
}

Value Engine::print(Token times, Expression what) {
	int64_t num = numberExpression(times).as.literal.as.number;
	return evaluateExpression(what, num).val;
}

Value Engine::execute(const char *file) {
	Token t;
	scanner = Scanner(file);
	while(true) {
		if(scanner.hasScanErrors()) {
			throw EngineException(t, "Error occurred while scanning!");
		}
		t = scanner.scanNextToken();
		if(t.type == TOKEN_EOF)
			return Value();
		// expect identifier in the beginning of a statement
		if(t.type != TOKEN_IDENTIFIER && t.type != TOKEN_print) {
			throw EngineException(t, "Expected identifier!");
		}
		if(t.type == TOKEN_IDENTIFIER) {
			consume(TOKEN_EQUAL, "Expected '=' after identifier!");
			rules[String::from(t, true)] = parseExpression();
		} else if(t.type == TOKEN_print) {
			consume(TOKEN_LEFT_PAREN, "Expected '(' after print!");
			Token t = consume(TOKEN_NUMBER,
			                  "Expected number as first argument to 'print'!");
			consume(TOKEN_COMMA,
			        "Expected ',' after first argument to 'print'!");
			Expression what = parseExpression();
			consume(TOKEN_RIGHT_PAREN, "Expected ')' after print!");
			return print(t, what);
		} else if(t.type == TOKEN_EOF) {
			break;
		}
	}
	return Value();
}