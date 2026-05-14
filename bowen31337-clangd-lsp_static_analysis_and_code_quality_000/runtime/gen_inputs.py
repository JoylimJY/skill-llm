import os
import random
import json

random.seed(42)

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "ecu_firmware",
    "ecu_firmware/src",
    "ecu_firmware/include",
    "ecu_firmware/tests",
    "ecu_firmware/docs",
    "ecu_firmware/scripts",
    "ecu_firmware/build",
    "ecu_firmware/third_party",
    "ecu_firmware/third_party/canbus",
    "ecu_firmware/third_party/canbus/include",
    "ecu_firmware/legacy",
    "ecu_firmware/legacy/v1",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor / supporting files ──────────────────────────────────────────

# Makefile (intentionally minimal, no compile_commands.json generation)
with open("ecu_firmware/Makefile", "w") as f:
    f.write("""\
CXX = g++
CXXFLAGS = -std=c++17
SRCS = src/throttle_controller.cpp src/sensor_fusion.cpp
OBJS = $(SRCS:.cpp=.o)
TARGET = ecu_firmware

all: $(TARGET)

$(TARGET): $(OBJS)
\t$(CXX) $(CXXFLAGS) -o $@ $^

%.o: %.cpp
\t$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
\trm -f $(OBJS) $(TARGET)
""")

# docs
with open("ecu_firmware/docs/architecture.md", "w") as f:
    f.write("# ECU Firmware Architecture\n\nThis document describes the high-level design of the ECU firmware.\n")

with open("ecu_firmware/docs/coding_standards.md", "w") as f:
    f.write("# Coding Standards\n\nAll C++ code must conform to MISRA-C++ where applicable.\n")

# scripts
with open("ecu_firmware/scripts/flash.sh", "w") as f:
    f.write("#!/bin/bash\necho 'Flashing firmware to target...'\n")

with open("ecu_firmware/scripts/run_tests.sh", "w") as f:
    f.write("#!/bin/bash\necho 'Running unit tests...'\n./ecu_firmware_test\n")

# third_party canbus stubs
with open("ecu_firmware/third_party/canbus/include/canbus.h", "w") as f:
    f.write("""\
#pragma once
#include <cstdint>

namespace canbus {
    struct Frame {
        uint32_t id;
        uint8_t  data[8];
        uint8_t  len;
    };
    bool send(const Frame& frame);
    bool recv(Frame& frame);
}
""")

# legacy stubs
with open("ecu_firmware/legacy/v1/old_throttle.cpp", "w") as f:
    f.write("// Legacy v1 throttle code — do not use\n#include <stdio.h>\nvoid old_throttle() { printf(\"old\\n\"); }\n")

with open("ecu_firmware/legacy/v1/old_throttle.h", "w") as f:
    f.write("#pragma once\nvoid old_throttle();\n")

# build dir placeholder
with open("ecu_firmware/build/.gitkeep", "w") as f:
    f.write("")

# ── main project header (well-formed, just needs formatting) ───────────────
# throttle_controller.hpp  — badly formatted
with open("ecu_firmware/include/throttle_controller.hpp", "w") as f:
    f.write("""\
#pragma once
#include<cstdint>
#include <string>

namespace ecu {

class ThrottleController{
public:
ThrottleController(uint8_t channel,float max_angle);
~ThrottleController();
bool   setAngle(float angle);
float  getAngle()  const;
void   reset();
private:
uint8_t channel_;
float   current_angle_;
float   max_angle_;
bool    is_initialized_;
};

}  // namespace ecu
""")

# sensor_fusion.hpp — badly formatted
with open("ecu_firmware/include/sensor_fusion.hpp", "w") as f:
    f.write("""\
#pragma once
#include <vector>
#include<cstdint>
#include <cmath>

namespace ecu{
struct SensorReading{
uint32_t timestamp_ms;
float    value;
uint8_t  sensor_id;
};

class SensorFusion{
public:
SensorFusion();
void addReading(const SensorReading& r);
float computeAverage() const;
float computeVariance() const;
private:
std::vector<SensorReading> readings_;
};
} // namespace ecu
""")

# ── main source files (badly formatted + fixable issues) ──────────────────
# throttle_controller.cpp — badly formatted, compiles cleanly after format
with open("ecu_firmware/src/throttle_controller.cpp", "w") as f:
    f.write("""\
#include "throttle_controller.hpp"
#include<stdexcept>
#include <algorithm>

namespace ecu{

ThrottleController::ThrottleController(uint8_t channel,float max_angle)
:channel_(channel),current_angle_(0.0f),max_angle_(max_angle),is_initialized_(true)
{
if(max_angle<=0.0f){
throw std::invalid_argument("max_angle must be positive");
}
}

ThrottleController::~ThrottleController(){}

bool ThrottleController::setAngle(float angle){
if(!is_initialized_) return false;
current_angle_=std::clamp(angle,0.0f,max_angle_);
return true;
}

float ThrottleController::getAngle() const{
return current_angle_;
}

void ThrottleController::reset(){
current_angle_=0.0f;
}

} // namespace ecu
""")

# sensor_fusion.cpp — badly formatted
with open("ecu_firmware/src/sensor_fusion.cpp", "w") as f:
    f.write("""\
#include "sensor_fusion.hpp"
#include<numeric>
#include <stdexcept>

namespace ecu{

SensorFusion::SensorFusion(){}

void SensorFusion::addReading(const SensorReading& r){
readings_.push_back(r);
}

float SensorFusion::computeAverage() const{
if(readings_.empty()) return 0.0f;
float sum=0.0f;
for(const auto& r:readings_){
sum+=r.value;
}
return sum/static_cast<float>(readings_.size());
}

float SensorFusion::computeVariance() const{
if(readings_.size()<2) return 0.0f;
float avg=computeAverage();
float var=0.0f;
for(const auto& r:readings_){
float diff=r.value-avg;
var+=diff*diff;
}
return var/static_cast<float>(readings_.size()-1);
}

} // namespace ecu
""")

# ── test file (badly formatted) ────────────────────────────────────────────
with open("ecu_firmware/tests/test_main.cpp", "w") as f:
    f.write("""\
#include "throttle_controller.hpp"
#include "sensor_fusion.hpp"
#include<cassert>
#include <iostream>

int main(){
ecu::ThrottleController tc(1,90.0f);
assert(tc.setAngle(45.0f));
assert(tc.getAngle()==45.0f);
tc.reset();
assert(tc.getAngle()==0.0f);

ecu::SensorFusion sf;
ecu::SensorReading r1{100,1.0f,0};
ecu::SensorReading r2{200,3.0f,1};
sf.addReading(r1);
sf.addReading(r2);
assert(sf.computeAverage()==2.0f);

std::cout<<"All tests passed!"<<std::endl;
return 0;
}
""")

# ── intentionally leave out: .clangd, compile_commands.json ───────────────
# The agent must create both of these.

print("Workspace generated successfully.")
print("Files created:")
for root, subdirs, files in os.walk("ecu_firmware"):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")