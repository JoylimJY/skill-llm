#!/usr/bin/env python3
import os
import json
import random

# Set deterministic seed
random.seed(42)

# Create scripts directory
os.makedirs('scripts', exist_ok=True)

# Create shadcn-components.tar.gz (minimal mock)
with open('scripts/shadcn-components.tar.gz', 'wb') as f:
    import tarfile
    import io
    
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        # Create minimal component structure
        components_content = '''
export { Button } from './button';
export { Card, CardContent, CardHeader, CardTitle } from './card';
export { Progress } from './progress';
export { Switch } from './switch';
export { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select';
export { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs';
'''
        
        info = tarfile.TarInfo('components/ui/index.ts')
        info.size = len(components_content.encode())
        tar.addfile(info, io.BytesIO(components_content.encode()))
        
        # Add utils
        utils_content = '''
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
'''
        info = tarfile.TarInfo('lib/utils.ts')
        info.size = len(utils_content.encode())
        tar.addfile(info, io.BytesIO(utils_content.encode()))
        
    tar_buffer.seek(0)
    f.write(tar_buffer.getvalue())

# Create requirements file with marker for validation
requirements = {
    "validation_marker": "FINANCE_DASHBOARD_TASK_2024",
    "required_features": [
        "expense_tracker_with_filtering",
        "budget_vs_actual_comparison", 
        "investment_portfolio_charts",
        "financial_goals_tracker",
        "theme_toggle_functionality"
    ],
    "ui_requirements": {
        "responsive_design": True,
        "modern_patterns": True,
        "interactive_charts": True,
        "progress_indicators": True
    }
}

with open('task_requirements.json', 'w') as f:
    json.dump(requirements, f, indent=2)

print("Generated input files for personal finance dashboard task")