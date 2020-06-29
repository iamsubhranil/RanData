#pragma once

#include <cstdlib>
#include <cstring>
#include <string>

#include "scanner.h"

struct Array; // essentially tuple, size must be predefined
struct String;
struct InterimValue;
struct Repeat;

// An yet to be evaluated function call
struct FunctionCall {
	TokenType name;
	Array *   args;

	static FunctionCall from(TokenType type) {
		FunctionCall f;
		f.name = type;
		f.args = NULL;
		return f;
	}
};

struct Value {
	// An identifier is also a string, yet we mark it
	// differently to denote it is something to
	// evaluate to the engine
	enum Type {
		Array,
		String,
		Identifier,
		Number,
		FunctionCall,
		Repeat,
		None
	} type;

	static const char *TypeStrings[7];

	union {
		struct FunctionCall func;
		struct Array *      arr;
		struct String *     str;
		struct Repeat *     rep;
		int64_t             number;
	} as;

	inline bool isArray() { return type == Array; }
	inline bool isString() { return type == String; }
	inline bool isIdentifier() { return type == Identifier; }
	inline bool isNumber() { return type == Number; }
	inline bool isFunctionCall() { return type == FunctionCall; }
	inline bool isRepeat() { return type == Repeat; }

	Value() : type(None) {}
	Value(struct String *str) {
		type   = String;
		as.str = str;
	}

	static Value identifier(struct String *str) {
		Value v = Value(str);
		v.type  = Identifier;
		return v;
	}

	Value(int64_t t) {
		as.number = t;
		type      = Number;
	}

	Value(struct FunctionCall f) {
		type    = FunctionCall;
		as.func = f;
	}

	Value(struct Array *s) {
		type   = Array;
		as.arr = s;
	}

	Value(struct Repeat *r) {
		type   = Repeat;
		as.rep = r;
	}
};

struct Repeat {
	int   size;
	Value val;

	static Repeat *from(Value v, int times) {
		Repeat *r = (Repeat *)malloc(sizeof(Repeat));
		r->size   = times;
		r->val    = v;
		return r;
	}

	inline Value &at(int idx) {
		(void)idx;
		return val;
	}
};

struct Array {
	int size;

	static Array *create(int s) {
		Array *arr = (Array *)malloc(sizeof(Array) + (sizeof(Value) * s));
		arr->size  = s;
		return arr;
	}

	static Array *resize(Array *old, int newSize) {
		Array *n =
		    (Array *)realloc(old, sizeof(Array) + (sizeof(Value) * newSize));
		n->size = newSize;
		return n;
	}

	inline Value &at(int idx) const { return values()[idx]; }
	inline Value *values() const { return ((Value *)(this + 1)); }
};

struct String {
	int hash_;
	int size;

	static int hashString(const char *s, int size) {
		int hash_ = 0;

		for(int i = 0; i < size; ++i) {
			hash_ += s[i];
			hash_ += (hash_ << 10);
			hash_ ^= (hash_ >> 6);
		}

		hash_ += (hash_ << 3);
		hash_ ^= (hash_ >> 11);
		hash_ += (hash_ << 15);

		return hash_;
	}

	static String *from(const char *source, int size,
	                    bool isIdentifier = false) {
		String *s =
		    (String *)malloc(sizeof(String) + sizeof(char) * (size + 1));
		s->size = size;
		// we only need the hash for identifiers, which are stored
		// in the result and rules cache
		if(isIdentifier)
			s->hash_ = hashString(source, size);
		char *dest = s->values();
		memcpy(dest, source, size);
		dest[size] = 0;
		return s;
	}

	static String *from(const char *source, bool isIdentifier = false) {
		return from(source, strlen(source), isIdentifier);
	}

	static String *fromNumber(int64_t number) {
		return from(std::to_string(number).c_str(), false);
	}

	static String *from(Token t, bool isIdentifier = false) {
		return from(t.start, t.length, isIdentifier);
	}

	// if own is true, it is indicated that the returned string
	// should be owned by the calling function, and maybe
	// modified. So, when returning a string, we make a copy
	// of it so that the original string stays untouched.
	static String *toString(Value v, bool own = false) {
		switch(v.type) {
			case Value::String:
				if(own)
					return v.as.str->copy();
				return v.as.str;
			case Value::Number: return fromNumber(v.as.number);
			case Value::Repeat: return toString(v.as.rep->val, own);
			default:
				// should not reach here
				return NULL;
		}
	}

	inline char *values() const { return (char *)(this + 1); }

	String *append(Value with) { return append(toString(with, false)); }

	static String *appendInPlace(String *from, Value with) {
		return appendInPlace(from, toString(with, false));
	}

	String *copy() {
		String *s = (String *)malloc(sizeof(String) + size + 1);
		memcpy(s, this, sizeof(String) + size + 1);
		return s;
	}

	String *lower() {
		for(int i = 0; i < size; i++) values()[i] = tolower(values()[i]);
		return this;
	}

	String *append(String *with) {
		int     totalSize = size + with->size;
		String *s =
		    (String *)malloc(sizeof(String) + (sizeof(char) * (totalSize + 1)));
		memcpy(s->values(), values(), size);
		memcpy(&(s->values()[size]), with->values(), with->size);
		s->values()[totalSize] = 0;
		s->size                = totalSize;
		// we don't hash the resulting string
		// s->hash_ = hashString(s->values(), totalSize);
		return s;
	}

	// 'from' must be heap allocated, the pointer may change.
	// so the variable it belongs to must be reassigned
	// after this call.
	static String *appendInPlace(String *from, String *with) {
		int     size = from->size;
		String *m    = (String *)realloc(
            from, sizeof(String) + (sizeof(char) * (size + with->size + 1)));
		memcpy(&(m->values()[size]), with->values(), with->size);
		m->values()[size + with->size] = 0;
		m->size += with->size;
		// we don't hash the resulting string
		// m->hash_ = hashString(m->values(), m->size);
		return m;
	}
};

struct StringHash {
	std::size_t operator()(const String *s) const { return s->hash_; }
};

struct StringEquals {
	bool operator()(const String *a, const String *b) const {
		return a->hash_ == b->hash_ && a->size == b->size &&
		       strncmp(a->values(), b->values(), a->size) == 0;
	}
};
