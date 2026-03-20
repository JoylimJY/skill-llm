#!/usr/bin/env python3
import os
import random
import json

# Set fixed seed for deterministic output
random.seed(42)

# Create scripts directory
os.makedirs('scripts', exist_ok=True)

# Create the shadcn-components.tar.gz (minimal version for testing)
import tarfile
import io

# Create minimal component structure
components_data = {
    'components/ui/button.tsx': '''import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }''',
    'components/ui/input.tsx': '''import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }''',
    'components/ui/card.tsx': '''import * as React from "react"
import { cn } from "@/lib/utils"

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-lg border bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
))
Card.displayName = "Card"

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

export { Card, CardHeader, CardTitle, CardContent }''',
    'lib/utils.ts': '''import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}'''
}

# Create tar.gz with components
with tarfile.open('scripts/shadcn-components.tar.gz', 'w:gz') as tar:
    for filepath, content in components_data.items():
        info = tarfile.TarInfo(filepath)
        info.size = len(content.encode('utf-8'))
        tar.addfile(info, io.BytesIO(content.encode('utf-8')))

# Copy the init script
with open('scripts/init-artifact.sh', 'w') as f:
    f.write(open('/workspace/scripts/init-artifact.sh', 'r').read())

# Copy the bundle script
with open('scripts/bundle-artifact.sh', 'w') as f:
    f.write(open('/workspace/scripts/bundle-artifact.sh', 'r').read())

os.chmod('scripts/init-artifact.sh', 0o755)
os.chmod('scripts/bundle-artifact.sh', 0o755)

# Create a requirements file that specifies the task details
requirements = {
    'task_type': 'task_management_app',
    'required_features': [
        'drag_and_drop',
        'multiple_columns',
        'add_edit_tasks',
        'due_dates',
        'dark_mode_toggle',
        'professional_design'
    ],
    'columns': ['To Do', 'In Progress', 'Done'],
    'marker_content': 'TaskManagementApp_Marker_2024'
}

with open('requirements.json', 'w') as f:
    json.dump(requirements, f, indent=2)

print('Generated input files for task management app creation task')