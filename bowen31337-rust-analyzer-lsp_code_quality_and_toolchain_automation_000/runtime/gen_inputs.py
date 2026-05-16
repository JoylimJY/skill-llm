import os
import textwrap

workspace = "/workspace"

# Create a realistic Rust project for a temperature sensor firmware library
project_dir = os.path.join(workspace, "sensor_firmware")
src_dir = os.path.join(project_dir, "src")
tests_dir = os.path.join(project_dir, "tests")
benches_dir = os.path.join(project_dir, "benches")
docs_dir = os.path.join(project_dir, "docs")
examples_dir = os.path.join(project_dir, "examples")
config_dir = os.path.join(project_dir, ".cargo")

for d in [src_dir, tests_dir, benches_dir, docs_dir, examples_dir, config_dir,
          os.path.join(src_dir, "filters"),
          os.path.join(src_dir, "calibration"),
          os.path.join(project_dir, "scripts")]:
    os.makedirs(d, exist_ok=True)

# Cargo.toml
cargo_toml = textwrap.dedent("""\
    [package]
    name = "sensor_firmware"
    version = "0.1.0"
    edition = "2021"

    [dependencies]

    [dev-dependencies]

    [[example]]
    name = "basic_usage"
    path = "examples/basic_usage.rs"
""")
with open(os.path.join(project_dir, "Cargo.toml"), "w") as f:
    f.write(cargo_toml)

# Main lib.rs — poorly formatted, with clippy warnings, and a logic bug
# Clippy issues:
#   1. `vec.len() == 0` instead of `vec.is_empty()`
#   2. `let x = x.clone()` unnecessary clone on Copy type (u32)
#   3. Redundant closure: `.map(|x| x.to_celsius())` where it could be `.map(SensorReading::to_celsius)` — actually let's use simpler ones
#   4. Using `if let` when a regular match is clearer — but let's keep it to clear clippy lints
# Logic bug: `to_fahrenheit` has wrong formula (missing +32)
lib_rs = """\
pub mod filters;
pub mod calibration;

/// Represents a raw sensor reading in millidegrees Celsius.
#[derive(Debug,Clone,PartialEq)]
pub struct SensorReading {
pub raw_value: i32,
pub sensor_id: u8,
}

impl SensorReading {
    pub fn new(raw_value:i32,sensor_id:u8)->Self{
        SensorReading{raw_value,sensor_id}
    }

    /// Convert millidegrees Celsius to degrees Celsius
    pub fn to_celsius(&self)->f64{
        self.raw_value as f64/1000.0
    }

    /// Convert millidegrees Celsius to degrees Fahrenheit
    pub fn to_fahrenheit(&self)->f64{
        let celsius=self.to_celsius();
        celsius*9.0/5.0
    }

    /// Check if reading is within a valid range (in degrees Celsius)
    pub fn is_valid(&self,min_c:f64,max_c:f64)->bool{
        let c=self.to_celsius();
        c>=min_c&&c<=max_c
    }
}

/// A batch of sensor readings
pub struct ReadingBatch {
    pub readings: Vec<SensorReading>,
}

impl ReadingBatch {
    pub fn new()->Self{
        ReadingBatch{readings:Vec::new()}
    }

    pub fn add(&mut self,reading:SensorReading){
        self.readings.push(reading);
    }

    /// Returns true if the batch has no readings
    pub fn is_empty_batch(&self)->bool{
        if self.readings.len()==0{
            return true;
        }
        false
    }

    /// Compute average temperature in Celsius
    pub fn average_celsius(&self)->Option<f64>{
        if self.readings.len()==0{
            return None;
        }
        let sum:f64=self.readings.iter().map(|r| r.to_celsius()).sum();
        let count=self.readings.len().clone();
        Some(sum/count as f64)
    }

    /// Returns readings that are valid within a given range
    pub fn valid_readings(&self,min_c:f64,max_c:f64)->Vec<&SensorReading>{
        let result:Vec<&SensorReading>=self.readings.iter().filter(|r| r.is_valid(min_c,max_c)).collect();
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_to_celsius(){
        let r=SensorReading::new(25000,1);
        assert_eq!(r.to_celsius(),25.0);
    }

    #[test]
    fn test_to_fahrenheit(){
        let r=SensorReading::new(0,1);
        // 0°C should be 32°F
        assert_eq!(r.to_fahrenheit(),32.0);
    }

    #[test]
    fn test_to_fahrenheit_boiling(){
        let r=SensorReading::new(100000,1);
        // 100°C should be 212°F
        assert_eq!(r.to_fahrenheit(),212.0);
    }

    #[test]
    fn test_batch_average(){
        let mut batch=ReadingBatch::new();
        batch.add(SensorReading::new(20000,1));
        batch.add(SensorReading::new(30000,1));
        assert_eq!(batch.average_celsius(),Some(25.0));
    }

    #[test]
    fn test_batch_empty(){
        let batch=ReadingBatch::new();
        assert!(batch.is_empty_batch());
        assert_eq!(batch.average_celsius(),None);
    }

    #[test]
    fn test_valid_readings(){
        let mut batch=ReadingBatch::new();
        batch.add(SensorReading::new(-5000,1));   // -5°C
        batch.add(SensorReading::new(25000,2));   //  25°C
        batch.add(SensorReading::new(85000,3));   //  85°C
        let valid=batch.valid_readings(0.0,80.0);
        assert_eq!(valid.len(),1);
        assert_eq!(valid[0].sensor_id,2);
    }
}
"""

with open(os.path.join(src_dir, "lib.rs"), "w") as f:
    f.write(lib_rs)

# filters/mod.rs — also poorly formatted with clippy issues
filters_mod = """\
/// Simple moving average filter for sensor readings
pub struct MovingAverage {
    window:usize,
    buffer:Vec<f64>,
}

impl MovingAverage {
    pub fn new(window:usize)->Self{
        MovingAverage{window,buffer:Vec::new()}
    }

    pub fn push(&mut self,value:f64)->f64{
        self.buffer.push(value);
        if self.buffer.len()>self.window{
            self.buffer.remove(0);
        }
        let sum:f64=self.buffer.iter().map(|x| x.clone()).sum();
        sum/self.buffer.len() as f64
    }

    pub fn is_full(&self)->bool{
        if self.buffer.len()==self.window{
            return true;
        }
        return false;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_moving_average(){
        let mut ma=MovingAverage::new(3);
        assert_eq!(ma.push(10.0),10.0);
        assert_eq!(ma.push(20.0),15.0);
        assert_eq!(ma.push(30.0),20.0);
        assert_eq!(ma.push(40.0),30.0);
    }

    #[test]
    fn test_is_full(){
        let mut ma=MovingAverage::new(2);
        ma.push(1.0);
        assert!(!ma.is_full());
        ma.push(2.0);
        assert!(ma.is_full());
    }
}
"""

with open(os.path.join(src_dir, "filters", "mod.rs"), "w") as f:
    f.write(filters_mod)

# calibration/mod.rs — poorly formatted
calibration_mod = """\
/// Calibration offset for a sensor
#[derive(Debug,Clone)]
pub struct CalibrationOffset {
    pub sensor_id:u8,
    pub offset_millidegrees:i32,
}

impl CalibrationOffset {
    pub fn new(sensor_id:u8,offset_millidegrees:i32)->Self{
        CalibrationOffset{sensor_id,offset_millidegrees}
    }

    pub fn apply(&self,raw_value:i32)->i32{
        raw_value+self.offset_millidegrees
    }
}

/// A registry of calibration offsets keyed by sensor_id
pub struct CalibrationRegistry {
    offsets:Vec<CalibrationOffset>,
}

impl CalibrationRegistry {
    pub fn new()->Self{
        CalibrationRegistry{offsets:Vec::new()}
    }

    pub fn register(&mut self,offset:CalibrationOffset){
        self.offsets.push(offset);
    }

    pub fn get(&self,sensor_id:u8)->Option<&CalibrationOffset>{
        let found:Vec<&CalibrationOffset>=self.offsets.iter().filter(|o| o.sensor_id==sensor_id).collect();
        if found.len()==0{
            return None;
        }
        Some(found[0])
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calibration_apply(){
        let cal=CalibrationOffset::new(1,500);
        assert_eq!(cal.apply(24500),25000);
    }

    #[test]
    fn test_registry_get(){
        let mut reg=CalibrationRegistry::new();
        reg.register(CalibrationOffset::new(3,100));
        let found=reg.get(3);
        assert!(found.is_some());
        assert_eq!(found.unwrap().offset_millidegrees,100);
        assert!(reg.get(99).is_none());
    }
}
"""

with open(os.path.join(src_dir, "calibration", "mod.rs"), "w") as f:
    f.write(calibration_mod)

# examples/basic_usage.rs
example_rs = """\
use sensor_firmware::{SensorReading,ReadingBatch};

fn main(){
    let readings=vec![
        SensorReading::new(22000,1),
        SensorReading::new(23500,2),
        SensorReading::new(21000,3),
    ];
    let mut batch=ReadingBatch::new();
    for r in readings{
        println!("Sensor {}: {:.2}°C = {:.2}°F",r.sensor_id,r.to_celsius(),r.to_fahrenheit());
        batch.add(r);
    }
    if let Some(avg)=batch.average_celsius(){
        println!("Average: {:.2}°C",avg);
    }
}
"""

with open(os.path.join(examples_dir, "basic_usage.rs"), "w") as f:
    f.write(example_rs)

# Distractor files
distractor_files = {
    os.path.join(project_dir, "scripts", "flash_firmware.sh"): "#!/bin/bash\necho 'Flashing firmware...'\n",
    os.path.join(project_dir, "scripts", "run_tests.sh"): "#!/bin/bash\necho 'Running tests...'\n",
    os.path.join(project_dir, "docs", "architecture.md"): "# Sensor Firmware Architecture\n\nThis document describes the firmware architecture.\n",
    os.path.join(project_dir, "docs", "calibration_procedure.md"): "# Calibration Procedure\n\nSteps for calibrating sensors.\n",
    os.path.join(project_dir, ".cargo", "config.toml"): "[build]\ntarget-dir = \"target\"\n",
    os.path.join(project_dir, "benches", "perf.rs"): "// Benchmarks placeholder\n",
    os.path.join(project_dir, "CHANGELOG.md"): "# Changelog\n\n## Unreleased\n- Initial implementation\n",
    os.path.join(project_dir, "scripts", "generate_report.py"): "#!/usr/bin/env python3\nprint('Generating report...')\n",
    os.path.join(project_dir, "docs", "sensor_specs.txt"): "NTC-103 Thermistor\nRange: -40C to +125C\nAccuracy: +/- 0.5C\n",
    os.path.join(project_dir, ".gitignore"): "/target\nCargo.lock\n*.swp\n",
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Project directory: {project_dir}")
print("Issues introduced:")
print("  1. to_fahrenheit() bug: missing +32 (returns wrong value)")
print("  2. Clippy: len()==0 should be is_empty() in multiple places")
print("  3. Clippy: .clone() on usize (Copy type) is redundant")
print("  4. Clippy: .map(|x| x.clone()) on f64 (Copy type) is redundant")
print("  5. All code is poorly formatted (missing spaces, wrong indentation)")
print("  6. No .rust-analyzer.json config file")