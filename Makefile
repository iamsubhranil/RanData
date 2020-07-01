override CXXFLAGS += -Wall -Wextra
override LDFLAGS +=

RM=rm -f
# $(wildcard *.cpp /xxx/xxx/*.cpp): get all .cpp files from the current directory and dir "/xxx/xxx/"
SRCS := $(wildcard *.cpp)
# $(patsubst %.cpp,%.o,$(SRCS)): substitute all ".cpp" file name strings to ".o" file name strings
OBJS := $(patsubst %.cpp,%.o,$(SRCS))

# Allows one to enable verbose builds with VERBOSE=1
V := @
ifeq ($(VERBOSE),1)
	V :=
endif

all: release

release: CXXFLAGS += -O3
release: LDFLAGS += -s
release: generator

profile: CXXFLAGS += -O2 -g3
profile: generator

debug: CXXFLAGS += -g3 -DDEBUG
debug: generator

ifeq ($(CXX),clang++)
clean_pgodata: clean
	$(V) rm -f default_*.profraw default.profdata
else
clean_pgodata: clean
	$(V) rm -f *.gcda objects/*.gcda
endif

pgo: CXXFLAGS+=-fprofile-generate -march=native
pgo: LDFLAGS+=-fprofile-generate -flto
pgo: | clean_pgodata release

ifeq ($(CXX),clang++)
merge_profraw:
	$(V) llvm-profdata merge --output=default.profdata default_*.profraw
else
merge_profraw:
endif

pgouse: merge_profraw
	$(V) $(MAKE) clean
	$(V) $(MAKE) release CXXFLAGS=-fprofile-use CXXFLAGS+=-march=native LDFLAGS+=-fprofile-use LDFLAGS+=-flto

generator: $(OBJS)
	$(V) $(MAKE) -C CargParser lib_release
	$(V) $(CXX) $(LDFLAGS) $(OBJS) CargParser/cargparser.o -o generator

depend: .depend

.depend: $(SRCS)
	$(RM) ./.depend
	$(CXX) $(CXXFLAGS) -MM $^>>./.depend;

clean:
	$(RM) $(OBJS)

distclean: clean
	$(RM) *~ .depend

include .depend

%.o: %.cpp
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) -c $< -o $@
