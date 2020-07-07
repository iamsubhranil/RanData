#include "engine.h"

#include "display.h"
#include <thread>

#define CALL_FUNCTION(func) ((this)->*func)

int Engine::argumentCounts[] = {
#define KEYWORD(x, y, z) z,
#include "keywords.h"
};

int Expression::ExpressionCounter = 0;

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
	Expression e = Expression(a, f);
	if(a.type == TOKEN_one_of_unique) {
		uniqueMutexes.resize(e.id + 1);
		uniqueMutexes[e.id] = new std::mutex();
	}
	return e;
}

// execution

Result Engine::numberExecute(Expression num, int times) {
	(void)times;
	return Result(Collection(num.as.literal), true);
}

Result Engine::stringExecute(Expression str, int times) {
	(void)times;
	return Result(Collection(str.as.literal), true);
}

Result Engine::identifierExecute(Expression id, int times, ResultMap &results,
                                 int offset) {
	Value iden = id.as.literal;
	if(results.contains(iden.as.str)) {
		return results[iden.as.str];
	} else if(!rules.contains(iden.as.str)) {
		throw EngineException("No such rule found!");
	}
	Expression repr = rules[iden.as.str];
	Result     res  = evaluateExpression(repr, times, results, offset);
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
		strings[i] = String::toString(args[i].val.at(row));
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

Result Engine::appendExecute(Expression t, Result *args, int count,
                             bool isConstant, int times, int offset) {
	(void)t;
	(void)offset;
	if(isConstant) {
		return Result(Collection(appendOneRow(args, count, 0)), true);
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
		return Result(Collection(res));
	}
}

Result Engine::lowerExecute(Expression t, Result *args, int count,
                            bool isConstant, int times, int offset) {
	(void)count;
	(void)t;
	(void)offset;
	if(isConstant) {
		return Result(
		    Collection(String::toString(args[0].val.at(0), true)->lower()),
		    true);
	} else {
		Array *res = Array::create(times);
		for(int i = 0; i < times; i++) {
			res->at(i) =
			    Value(String::toString(args[0].val.at(i), true)->lower());
		}
		return Result(Collection(res));
	}
}

Result Engine::number_betweenExecute(Expression t, Result *args, int count,
                                     bool isConstant, int times, int offset) {
	(void)count;
	(void)offset;
	if(isConstant) {
		if(!validateType(args[0].val.at(0), Value::Number) ||
		   !validateType(args[1].val.at(0), Value::Number)) {
			throw EngineException(t.token, "Both arguments of 'number_between' "
			                               "must be valid numbers!");
		}
		Array *res = Array::create(times);
		Random random;
		random.setIntGenerateRange(args[0].val.at(0).as.number,
		                           args[1].val.at(0).as.number);
		for(int i = 0; i < times; i++) {
			res->at(i) = Value(random.nextIntInRange());
		}
		return Result(Collection(res));
	} else {
		Array *res = Array::create(times);
		Random random;
		for(int i = 0; i < times; i++) {
			Value v1 = args[0].val.at(i);
			Value v2 = args[1].val.at(i);
			if(!validateType(v1, Value::Number) ||
			   !validateType(v2, Value::Number)) {
				throw EngineException(
				    t.token, "Both arguments of 'number_between' must be valid "
				             "numbers!");
			}
			random.setIntGenerateRange(v1.as.number, v2.as.number);
			res->at(i) = Value(random.nextIntInRange());
		}
		return Result(Collection(res));
	}
}

Result Engine::number_uptoExecute(Expression t, Result *args, int count,
                                  bool isConstant, int times, int offset) {
	(void)count;
	(void)offset;
	if(isConstant) {
		if(!validateType(args[0].val.at(0), Value::Number)) {
			throw EngineException(
			    t.token, "Argument of 'number_upto' must be a valid number!");
		}
		Array *res = Array::create(times);
		Random random;
		random.setIntGenerateRange(0, args[0].val.at(0).as.number);
		for(int i = 0; i < times; i++) {
			res->at(i) = Value(random.nextIntInRange());
		}
		return Result(Collection(res));
	} else {
		Array *res = Array::create(times);
		Random random;
		for(int i = 0; i < times; i++) {
			Value v1 = args[0].val.at(i);
			if(!validateType(v1, Value::Number)) {
				throw EngineException(
				    t.token, "Argument of 'number_upto' must be a valid "
				             "number!");
			}
			random.setIntGenerateRange(0, v1.as.number);
			res->at(i) = Value(random.nextIntInRange());
		}
		return Result(Collection(res));
	}
}

Result Engine::one_ofExecute(Expression t, Result *args, int count,
                             bool isConstant, int times, int offset) {
	(void)t;
	(void)offset;
	if(isConstant) {
		Array *res = Array::create(times);
		Random random;
		random.setIntGenerateRange(0, count - 1);
		for(int i = 0; i < times; i++) {
			res->at(i) = args[random.nextIntInRange()].val.at(0);
		}
		return Result(Collection(res));
	} else {
		Array *res = Array::create(times);
		Random random;
		random.setIntGenerateRange(0, count - 1);
		for(int i = 0; i < times; i++) {
			res->at(i) = args[random.nextIntInRange()].val.at(i);
		}
		return Result(Collection(res));
	}
	return Result(Value());
}

#include <iostream>

Result Engine::one_of_uniqueExecute(Expression t, Result *args, int count,
                                    bool isConstant, int times, int offset) {
	// take the mutex
	std::unique_lock<std::mutex> guard(*uniqueMutexes[t.id]);
	if(!uniqueDictionary.contains(t.id)) {
		uniqueDictionary[t.id] = new HashSet<Tuple, TupleHash, TupleEquals>();
	}
	HashSet<Tuple, TupleHash, TupleEquals> *selectedSet =
	    uniqueDictionary[t.id];
	std::cout << "Generating unique for expr " << t.id << " on thread "
	          << std::this_thread::get_id() << "\n";
	if(isConstant) {
		if(count < times) {
			throw EngineException(t.token,
			                      "Not enough unique values to generate!");
		}
		Random random;
		random.setIntGenerateRange(0, count - 1);
		Array *res = Array::create(times);
		int    i   = 0;
		while(i < times) {
			int   yidx = random.nextIntInRange();
			Tuple t    = Tuple(offset, yidx);
			if(selectedSet->contains(t))
				continue;
			selectedSet->insert(t);
			res->at(i) = args[yidx].val.at(0);
			i++;
		}
		return Result(Collection(res));
	} else {
		Random random;
		random.setIntGenerateRange(0, count - 1);
		Random rand2;
		rand2.setIntGenerateRange(0, times - 1);
		// is it possible to not have enough values?
		Array *res = Array::create(times);
		int    i   = 0;
		while(i < times) {
			int   yidx = random.nextIntInRange();
			int   xidx = rand2.nextIntInRange();
			Tuple t(offset + xidx, yidx);
			// printf("here i: %d times: %d size: %lu x: %d y: %d\n", i, times,
			//       selectedSet->size(), xidx, yidx);
			if(selectedSet->contains(t))
				continue;
			selectedSet->insert(t);
			res->at(i) = args[yidx].val.at(xidx);
			i++;
		}
		return Result(Collection(res));
	}
}

Result Engine::printExecute(Expression t, Result *args, int count,
                            bool isConstant, int times, int offset) {
	(void)t;
	(void)args;
	(void)count;
	(void)isConstant;
	(void)times;
	(void)offset;
	return Result(Value());
}

Result Engine::functionExecute(Expression e, int times, ResultMap &ruleResults,
                               int offset) {
	Result *results =
	    (Result *)malloc(sizeof(Result) * e.as.functionCall.count);
	bool isConstant = true;
	for(int i = 0; i < e.as.functionCall.count; i++) {
		results[i] = evaluateExpression(e.as.functionCall.args[i], times,
		                                ruleResults, offset);
		isConstant = isConstant & results[i].isConstant;
	}
	Result res;
	switch(e.as.functionCall.name) {
#define KEYWORD(x, y, z)                                                  \
	case TOKEN_##x:                                                       \
		res = x##Execute(e, results, e.as.functionCall.count, isConstant, \
		                 times, offset);                                  \
		break;
#include "keywords.h"
		default:
			panic("Invalid function type '%d' passed for execution!",
			      e.as.functionCall.name);
			break;
	}
	free(results);
	return res;
}

Result Engine::evaluateExpression(Expression e, int times, ResultMap &results,
                                  int offset) {
	switch(e.type) {
		case Expression::FunctionCall:
			return functionExecute(e, times, results, offset);
		case Expression::Literal: {
			Value v = e.as.literal;
			switch(v.type) {
				case Value::Number: return numberExecute(e, times);
				case Value::String: return stringExecute(e, times);
				case Value::Identifier:
					return identifierExecute(e, times, results, offset);
				default:
					panic("Invalid value type '%d' passed for execution!",
					      v.type);
			}
		}
	}
}

void Engine::evaluateExpression1(Expression ex, int num,
                                 std::promise<Result> *result, int offset) {
	ResultMap resultCache;
	result->set_value(evaluateExpression(ex, num, resultCache, offset));
}

bool Engine::validateType(Value arg, Value::Type type) {
	if(arg.type == type)
		return true;
	return false;
}

CountedCollection Engine::print(Token times, Expression what) {
	int64_t              num = numberExpression(times).as.literal.as.number;
	std::thread          threads[numProcesses];
	std::promise<Result> results[numProcesses];
	int                  partCount[numProcesses];
	int                  part = num / numProcesses;
	int                  done = 0;
	for(int i = 0; i < numProcesses - 1; i++) {
		threads[i] = std::thread(&Engine::evaluateExpression1, this, what, part,
		                         &results[i], done);
		partCount[i] = part;
		done += part;
	}
	threads[numProcesses - 1] =
	    std::thread(&Engine::evaluateExpression1, this, what, num - done,
	                &results[numProcesses - 1], done);
	partCount[numProcesses - 1] = num - done;
	for(int i = 0; i < numProcesses; i++) {
		threads[i].join();
	}
	CountedCollection cc;
	cc.type = CountedCollection::NESTED;
	cc.size = numProcesses;
	cc.nest =
	    (CountedCollection *)malloc(sizeof(CountedCollection) * numProcesses);
	for(int i = 0; i < numProcesses; i++) {
		cc.nest[i].type = CountedCollection::SINGLE;
		cc.nest[i].c    = results[i].get_future().get().val;
		cc.nest[i].size = partCount[i];
	}
	return cc;
}

CountedCollection Engine::execute(const char *file) {
	Token t;
	scanner = Scanner(file);
	while(true) {
		if(scanner.hasScanErrors()) {
			throw EngineException(t, "Error occurred while scanning!");
		}
		t = scanner.scanNextToken();
		if(t.type == TOKEN_EOF)
			return CountedCollection();
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
	return CountedCollection();
}
