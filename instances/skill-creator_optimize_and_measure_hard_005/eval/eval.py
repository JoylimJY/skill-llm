import os
import sys
import json
import subprocess
import time
import statistics
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

def check_file_exists(filepath, name):
    if os.path.exists(filepath):
        return {"name": f"{name} exists", "passed": True, "detail": f"Found {filepath}"}
    else:
        return {"name": f"{name} exists", "passed": False, "detail": f"Missing {filepath}"}

def check_optimization_markers(workspace_dir):
    """Check if code contains optimization markers and evidence of improvements"""
    checks = []
    
    # Look for common optimization files
    optimization_files = ['app.py', 'optimized_app.py', 'app_optimized.py', 'main.py']
    optimized_file = None
    
    for filename in optimization_files:
        filepath = os.path.join(workspace_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
                # Check if it's an optimized version (should have performance markers but improvements)
                if 'MARKER: PERFORMANCE_ENDPOINT_START' in content:
                    optimized_file = filepath
                    break
    
    if optimized_file:
        with open(optimized_file, 'r') as f:
            content = f.read()
            
        # Check for common optimization techniques
        optimizations_found = []
        
        if 'cache' in content.lower() or 'redis' in content.lower():
            optimizations_found.append('caching')
        
        if 'index' in content.lower() or 'dict' in content and 'defaultdict' not in content:
            optimizations_found.append('indexing')
            
        if content.count('for ') < 5:  # Original has many nested loops
            optimizations_found.append('loop_optimization')
            
        if 'numpy' in content or 'vectoriz' in content.lower():
            optimizations_found.append('vectorization')
            
        if len(optimizations_found) >= 2:
            checks.append({
                "name": "Code optimizations applied", 
                "passed": True, 
                "detail": f"Found optimizations: {', '.join(optimizations_found)}"
            })
        else:
            checks.append({
                "name": "Code optimizations applied", 
                "passed": False, 
                "detail": f"Limited optimizations found: {', '.join(optimizations_found)}"
            })
    else:
        checks.append({
            "name": "Optimized code exists", 
            "passed": False, 
            "detail": "No optimized app file found"
        })
    
    return checks

def check_performance_analysis(workspace_dir):
    """Check for performance analysis artifacts"""
    checks = []
    
    # Look for profiling outputs
    profile_files = []
    benchmark_files = []
    
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            if any(keyword in file.lower() for keyword in ['profile', 'perf', 'benchmark', 'timing']):
                if any(ext in file for ext in ['.txt', '.json', '.csv', '.html', '.png']):
                    if 'benchmark' in file.lower() or 'performance' in file.lower():
                        benchmark_files.append(file)
                    else:
                        profile_files.append(file)
    
    if profile_files:
        checks.append({
            "name": "Profiling analysis performed", 
            "passed": True, 
            "detail": f"Found profiling files: {', '.join(profile_files[:3])}"
        })
    else:
        checks.append({
            "name": "Profiling analysis performed", 
            "passed": False, 
            "detail": "No profiling output files found"
        })
    
    if benchmark_files:
        checks.append({
            "name": "Performance benchmarks created", 
            "passed": True, 
            "detail": f"Found benchmark files: {', '.join(benchmark_files[:3])}"
        })
    else:
        checks.append({
            "name": "Performance benchmarks created", 
            "passed": False, 
            "detail": "No benchmark result files found"
        })
    
    return checks

def test_actual_performance(workspace_dir):
    """Attempt to test the actual performance if possible"""
    checks = []
    
    # Look for the optimized app and try to run a quick test
    app_files = ['app.py', 'optimized_app.py', 'app_optimized.py', 'main.py']
    
    for app_file in app_files:
        app_path = os.path.join(workspace_dir, app_file)
        if os.path.exists(app_path):
            try:
                # Start the app in background
                proc = subprocess.Popen(
                    [sys.executable, app_file], 
                    cwd=workspace_dir,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                
                # Wait a bit for startup
                time.sleep(2)
                
                # Test a few requests
                response_times = []
                base_url = 'http://localhost:5000'
                
                for i in range(5):
                    try:
                        start = time.time()
                        response = requests.get(f'{base_url}/api/metrics', timeout=3)
                        end = time.time()
                        
                        if response.status_code == 200:
                            response_times.append(end - start)
                    except:
                        pass
                
                # Kill the process
                proc.terminate()
                proc.wait()
                
                if response_times:
                    avg_time = statistics.mean(response_times)
                    if avg_time < 0.5:  # Less than 500ms is decent improvement
                        checks.append({
                            "name": "Performance improvement verified", 
                            "passed": True, 
                            "detail": f"Average response time: {avg_time:.3f}s"
                        })
                    else:
                        checks.append({
                            "name": "Performance improvement verified", 
                            "passed": False, 
                            "detail": f"Response time still high: {avg_time:.3f}s"
                        })
                    break
                        
            except Exception as e:
                continue
    
    if not any(check['name'] == 'Performance improvement verified' for check in checks):
        checks.append({
            "name": "Performance improvement verified", 
            "passed": False, 
            "detail": "Could not test performance improvements directly"
        })
    
    return checks

def check_report_quality(workspace_dir):
    """Check for comprehensive performance report"""
    checks = []
    
    # Look for report files
    report_files = []
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            if any(keyword in file.lower() for keyword in ['report', 'analysis', 'summary', 'results']):
                if any(ext in file for ext in ['.md', '.txt', '.html', '.pdf']):
                    report_files.append(os.path.join(root, file))
    
    comprehensive_report = False
    
    for report_file in report_files:
        try:
            with open(report_file, 'r') as f:
                content = f.read().lower()
                
            # Check for key elements of a good performance report
            has_before_after = 'before' in content and 'after' in content
            has_metrics = any(metric in content for metric in ['response time', 'throughput', 'rps', 'latency'])
            has_bottlenecks = any(word in content for word in ['bottleneck', 'optimization', 'improvement'])
            
            if has_before_after and has_metrics and has_bottlenecks and len(content) > 500:
                comprehensive_report = True
                break
        except:
            continue
    
    if comprehensive_report:
        checks.append({
            "name": "Comprehensive performance report", 
            "passed": True, 
            "detail": "Found detailed performance analysis report"
        })
    else:
        checks.append({
            "name": "Comprehensive performance report", 
            "passed": False, 
            "detail": "No comprehensive performance report found"
        })
    
    return checks

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Usage", "passed": False, "detail": "Please provide workspace directory path"}]}))
        return
    
    workspace_dir = sys.argv[1]
    
    if not os.path.exists(workspace_dir):
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Workspace exists", "passed": False, "detail": f"Directory {workspace_dir} not found"}]}))
        return
    
    all_checks = []
    
    # Check for optimization evidence
    all_checks.extend(check_optimization_markers(workspace_dir))
    
    # Check for performance analysis
    all_checks.extend(check_performance_analysis(workspace_dir))
    
    # Check for comprehensive report
    all_checks.extend(check_report_quality(workspace_dir))
    
    # Attempt to test actual performance (optional)
    all_checks.extend(test_actual_performance(workspace_dir))
    
    # Calculate overall score
    passed_checks = sum(1 for check in all_checks if check["passed"])
    total_checks = len(all_checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Overall pass requires significant improvements
    overall_passed = score >= 0.7 and passed_checks >= 4
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": all_checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()