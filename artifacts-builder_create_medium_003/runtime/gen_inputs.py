import os

# Generate minimal input files for a React + Vite + Tailwind + shadcn/ui project named 'multi-route-artifact'

os.makedirs('multi-route-artifact/src/components/ui', exist_ok=True)
os.makedirs('multi-route-artifact/src/lib', exist_ok=True)
os.makedirs('multi-route-artifact/src/hooks', exist_ok=True)

# index.html with marker content
index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>multi-route-artifact</title>
</head>
<body>
  <div id="root"></div>
</body>
</html>'''
with open('multi-route-artifact/index.html', 'w') as f:
    f.write(index_html)

# minimal tsconfig.json
tsconfig_json = '''{
  "compilerOptions": {
    "target": "ESNext",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ESNext"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": false,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  },
  "include": ["src"]
}
'''
with open('multi-route-artifact/tsconfig.json', 'w') as f:
    f.write(tsconfig_json)

# postcss.config.js
postcss = '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'''
with open('multi-route-artifact/postcss.config.js', 'w') as f:
    f.write(postcss)

# tailwind.config.js
# Avoid purple gradients, centered layouts, uniform rounded corners, and Inter font
# Provide minimal Tailwind config with shadcn/ui theme 
tailwind_config = '''/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#111827', foreground: '#f9fafb' },
        secondary: { DEFAULT: '#374151', foreground: '#e5e7eb' },
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem',
        sm: '0.25rem',
      },
    },
  },
  plugins: [],
}
'''
with open('multi-route-artifact/tailwind.config.js', 'w') as f:
    f.write(tailwind_config)

# src/index.css with Tailwind directives and no Inter font
index_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: white;
  color: #111827;
}
'''

os.makedirs('multi-route-artifact/src', exist_ok=True)
with open('multi-route-artifact/src/index.css', 'w') as f:
    f.write(index_css)

# src/main.tsx bootstrapping React app
main_tsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
'''
with open('multi-route-artifact/src/main.tsx', 'w') as f:
    f.write(main_tsx)

# src/App.tsx with routing, state, forms, accordion per user request
app_tsx = '''
import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { Card } from './components/ui/card'
import { Button } from './components/ui/button'
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from './components/ui/accordion'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Input } from './components/ui/input'
import { Label } from './components/ui/label'

const userSchema = z.object({
  username: z.string().min(3, { message: 'Username must have at least 3 characters' }),
  email: z.string().email({ message: 'Invalid email address' }),
})

type UserForm = z.infer<typeof userSchema>

export default function App() {
  const [items, setItems] = useState(["Item 1", "Item 2", "Item 3"])

  const addItem = () => {
    setItems(prev => [...prev, `Item ${prev.length + 1}`])
  }

  return (
    <BrowserRouter>
      <header className="p-4 flex gap-4 bg-gray-100">
        <Link className="text-blue-600 hover:underline" to="/">Home</Link>
        <Link className="text-blue-600 hover:underline" to="/profile">Profile</Link>
        <Link className="text-blue-600 hover:underline" to="/settings">Settings</Link>
      </header>
      <main className="p-4">
        <Routes>
          <Route path="/" element={<Home items={items} addItem={addItem} />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

function Home({ items, addItem }: { items: string[], addItem: () => void }) {
  return (
    <Card className="max-w-lg">
      <h2 className="text-xl font-semibold mb-2">Home</h2>
      <ul className="mb-4 list-disc list-inside">
        {items.map((item, i) => <li key={i}>{item}</li>)}
      </ul>
      <Button onClick={addItem}>Add Item</Button>
    </Card>
  )
}

function Profile() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UserForm>({ resolver: zodResolver(userSchema) })

  const onSubmit = (data: UserForm) => alert(JSON.stringify(data))

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-md space-y-4">
      <div>
        <Label htmlFor="username">Username</Label>
        <Input id="username" {...register('username')} />
        {errors.username && <p className="text-red-600 text-sm">{errors.username.message}</p>}
      </div>
      <div>
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" {...register('email')} />
        {errors.email && <p className="text-red-600 text-sm">{errors.email.message}</p>}
      </div>
      <Button type="submit">Submit</Button>
    </form>
  )
}

function Settings() {
  return (
    <Accordion type="single" collapsible defaultValue="item-1" className="max-w-lg">
      <AccordionItem value="item-1">
        <AccordionTrigger>Section 1</AccordionTrigger>
        <AccordionContent>This is the content of section one.</AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>Section 2</AccordionTrigger>
        <AccordionContent>This is some more detail in section two.</AccordionContent>
      </AccordionItem>
    </Accordion>
  )
}
'''
with open('multi-route-artifact/src/App.tsx', 'w') as f:
    f.write(app_tsx)

# dummy placeholder UI components (to simulate shadcn/ui imports for eval)
# In real use they would come from installed packages.
# We provide minimal dummy implementations to not break TypeScript compilation.
ui_components = {
    'card.tsx': '''
import React, { ReactNode } from 'react'
export function Card({ children, className }: { children?: ReactNode, className?: string }) {
  return <div className={`border rounded-md p-4 bg-white ${className ?? ''}`}>{children}</div>
}
''',
    'button.tsx': '''
import React, { ReactNode, ButtonHTMLAttributes } from 'react'
export function Button(props: ButtonHTMLAttributes<HTMLButtonElement> & { children?: ReactNode }) {
  return <button {...props} className={`px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none ${props.className ?? ''}`} />
}
''',
    'accordion.tsx': '''
import React, { ReactNode } from 'react'
export function Accordion({ children, className }: { children?: ReactNode, className?: string }) {
  return <div className={className}>{children}</div>
}
export function AccordionItem({ children, value }: { children?: ReactNode, value: string }) {
  return <div>{children}</div>
}
export function AccordionTrigger({ children }: { children?: ReactNode }) {
  return <button className="font-semibold mb-1">{children}</button>
}
export function AccordionContent({ children }: { children?: ReactNode }) {
  return <div className="mb-3 pl-4 text-gray-700">{children}</div>
}
''',
    'input.tsx': '''
import React, { InputHTMLAttributes } from 'react'
export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`border rounded px-2 py-1 w-full ${props.className ?? ''}`} />
}
''',
    'label.tsx': '''
import React, { LabelHTMLAttributes } from 'react'
export function Label(props: LabelHTMLAttributes<HTMLLabelElement>) {
  return <label {...props} className={`block mb-1 font-medium ${props.className ?? ''}`} />
}
'''
}

for filename, content in ui_components.items():
    with open(f'multi-route-artifact/src/components/ui/{filename}', 'w') as f:
        f.write(content)

print("Input files for 'multi-route-artifact' generated successfully.")
