#pragma once

#include <random>

struct Random {
	std::random_device                     rand_dev;
	std::mt19937                           generator;
	std::uniform_int_distribution<int64_t> unifromIntDist;

	Random() { generator = std::mt19937(rand_dev()); }

	void setIntGenerateRange(int64_t from, int64_t to) {
		unifromIntDist = std::uniform_int_distribution<int64_t>(from, to);
	}

	int64_t nextIntInRange() { return unifromIntDist(generator); }
};
