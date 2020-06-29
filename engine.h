#pragma once
#include "hashmap.h"
#include "randutils.h"
#include "scanner.h"
#include "values.h"

struct Expression;
// An yet to be evaluated function call
struct FunctionCall {
	TokenType   name;
	Expression *args;
	int         count;

	static FunctionCall from(TokenType type) {
		FunctionCall f;
		f.name = type;
		f.args = NULL;
		return f;
	}

	FunctionCall() : name(TOKEN_ERROR), args(NULL), count(0) {}
};

struct Expression {
	Token token;
	int   id; // to denote an unique expression

	static int ExpressionCounter;

	enum Type { Literal, FunctionCall } type;

	union ExpressionContent {
		Value               literal;
		struct FunctionCall functionCall;
		ExpressionContent(Value v) : literal(v) {}
		ExpressionContent(struct FunctionCall f) : functionCall(f) {}
	} as;

	Expression()
	    : token(Token::PlaceholderToken), id(ExpressionCounter++),
	      type(Literal), as(Value()) {}
	Expression(Token t, Value v)
	    : token(t), id(ExpressionCounter++), type(Literal), as(v) {}
	Expression(Token t, struct FunctionCall f)
	    : token(t), id(ExpressionCounter++), type(FunctionCall), as(f) {}
};

struct Result {
	Value val;
	bool  isConstant;

	Result() : val(), isConstant(false) {}
	Result(Value v) : val(v), isConstant(false) {}
	Result(Value v, bool isc) : val(v), isConstant(isc) {}
};

using Tuple = std::tuple<int, int>;

struct TupleHash {
	std::size_t operator()(const Tuple &t) const {
		return std::get<0>(t) * 10 + std::get<1>(t);
	}
};

struct TupleEquals {
	bool operator()(const Tuple &a, const Tuple &b) const {
		return std::get<0>(a) == std::get<0>(b) &&
		       std::get<1>(a) == std::get<1>(b);
	}
};

struct Engine {
	// parses an expression and returns a representation
	// of its structure
	typedef Expression (Engine::*ExpressionRule)(Token ex);

	Scanner                                                 scanner;
	Random                                                  random;
	HashMap<String *, Expression, StringHash, StringEquals> rules;
	HashMap<String *, Result, StringHash, StringEquals>     results;
	// maps an expression id to a set of generated indices
	// HashMap<int, HashSet<Tuple> *, TupleHash, TupleEquals> uniqueDictionary;

	Engine() : scanner(NULL, ""), random() {}
	Token      consume(TokenType t, const char *message);
	Expression parseExpression(Token t);
	Expression parseExpression();
	Value      execute(const char *file);
	Value      print(Token times, Expression what);

	// returns ith value from the collection
	static Value getAt(Value v, int idx);

	// expression parsers
	Expression            identifierExpression(Token ex);
	Expression            stringExpression(Token ex);
	Expression            numberExpression(Token ex);
	Expression            functionExpression(Token ex);
	static ExpressionRule expressionRules[];

	// expression evaluators
	Result evaluateExpression(Expression e, int times);
	Result identifierExecute(Expression iden, int times);
	Result stringExecute(Expression str, int times);
	Result numberExecute(Expression num, int times);
	Result functionExecute(Expression e, int times);
#define KEYWORD(x, y, z)                                       \
	Result x##Execute(Expression expr, Result *args, int argc, \
	                  bool isConstant, int times);
#include "keywords.h"

	// validates whether the given value contains arguments
	// of the same type
	bool validateType(Value arg, Value::Type type);

	static int argumentCounts[];
};

class EngineException : public std::runtime_error {
  private:
	Token t;

  public:
	EngineException() : runtime_error("Error occurred while generating!") {}
	EngineException(const char *message)
	    : runtime_error(message), t(Token::PlaceholderToken) {}
	EngineException(Token to, const char *msg) : runtime_error(msg), t(to) {}
	virtual const char *what() const throw() {
		t.highlight(true, "At ", Token::ERROR);
		return runtime_error::what();
	}
	Token getToken() { return t; }
};
