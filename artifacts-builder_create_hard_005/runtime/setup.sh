#!/bin/bash

# Run the init archive script to create the project
bash scripts/init-artifact.sh multi-component-dashboard

cd multi-component-dashboard

# Inject routing and artifact code for multi-page dashboard with shadcn/ui components

# Install react-router-dom
pnpm add react-router-dom

# Update src/main.tsx to setup React Router DOM
cat > src/main.tsx << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
EOF

# Create src/App.tsx with Dashboard, Settings, Routing, and shadcn components
cat > src/App.tsx << 'EOF'
import React from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from './components/ui/accordion'
import { Tabs, TabsList, TabsTrigger, TabsContent } from './components/ui/tabs'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from './components/ui/card'
import { Button } from './components/ui/button'
import { Dialog, DialogTrigger, DialogContent, DialogTitle, DialogDescription, DialogClose } from './components/ui/dialog'
import { Input } from './components/ui/input'
import { Checkbox } from './components/ui/checkbox'
import { Switch } from './components/ui/switch'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'

const schema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  notifications: z.boolean(),
})

type FormData = z.infer<typeof schema>

function Dashboard() {
  return (
    <div className="p-4">
      <nav className="mb-4 flex gap-4">
        <Link className="text-blue-600 underline" to="/">Dashboard</Link>
        <Link className="text-blue-600 underline" to="/settings">Settings</Link>
      </nav>
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <Card className="flex-1">
          <CardHeader>
            <CardTitle>Users</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">1,245</p>
            <p>Active this month</p>
          </CardContent>
          <CardFooter>
            <Button size="sm">View Details</Button>
          </CardFooter>
        </Card>
        <Card className="flex-1">
          <CardHeader>
            <CardTitle>Sales</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">$76,432</p>
            <p>Income generated</p>
          </CardContent>
          <CardFooter>
            <Button size="sm">View Report</Button>
          </CardFooter>
        </Card>
        <Card className="flex-1">
          <CardHeader>
            <CardTitle>Feedback</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">342</p>
            <p>New reviews</p>
          </CardContent>
          <CardFooter>
            <Button size="sm">Read Feedback</Button>
          </CardFooter>
        </Card>
      </div>

      <Accordion type="single" collapsible>
        <AccordionItem value="details">
          <AccordionTrigger>More Details</AccordionTrigger>
          <AccordionContent>
            <Tabs defaultValue="overview" className="mt-2">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="stats">Stats</TabsTrigger>
                <TabsTrigger value="logs">Logs</TabsTrigger>
              </TabsList>
              <TabsContent value="overview">
                <p>This is the overview tab with high level info.</p>
              </TabsContent>
              <TabsContent value="stats">
                <p>Here are detailed stats and charts.</p>
              </TabsContent>
              <TabsContent value="logs">
                <p>Log entries and recent activities.</p>
              </TabsContent>
            </Tabs>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  )
}

function Settings() {
  const navigate = useNavigate()
  const { register, handleSubmit, formState: { errors }, watch } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      username: '',
      email: '',
      notifications: true,
    },
  })

  const onSubmit = (data: FormData) => {
    alert('Form submitted with: ' + JSON.stringify(data))
  }

  return (
    <div className="p-4 max-w-lg">
      <nav className="mb-4 flex gap-4">
        <Link className="text-blue-600 underline" to="/">Dashboard</Link>
        <Link className="text-blue-600 underline" to="/settings">Settings</Link>
      </nav>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <label htmlFor="username" className="block font-semibold mb-1">Username</label>
          <Input id="username" {...register('username')} />
          {errors.username && <p className="text-red-600 mt-1">{errors.username.message}</p>}
        </div>
        <div>
          <label htmlFor="email" className="block font-semibold mb-1">Email</label>
          <Input id="email" type="email" {...register('email')} />
          {errors.email && <p className="text-red-600 mt-1">{errors.email.message}</p>}
        </div>
        <div className="flex items-center space-x-2">
          <Checkbox id="notifications" {...register('notifications')} />
          <label htmlFor="notifications">Enable notifications</label>
        </div>
        <div className="flex items-center space-x-2">
          <Switch checked={watch('notifications')} onCheckedChange={() => {}} />
          <span>Toggle notifications</span>
        </div>
        <Button type="submit">Save Settings</Button>
      </form>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
  )
}
EOF

# Create src/components/ui index to export shadcn components
mkdir -p src/components/ui

# Create minimal UI exports as passthrough from shadcn components installed in node_modules
# In practice, the user would import from shadcn components extraction in src/components/ui ...
# For test simplicity, create passthrough exports for used components.

cat > src/components/ui/accordion.tsx <<'EOF'
export { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '@radix-ui/react-accordion'
EOF

cat > src/components/ui/tabs.tsx <<'EOF'
export { Tabs, TabsList, TabsTrigger, TabsContent } from '@radix-ui/react-tabs'
EOF

cat > src/components/ui/card.tsx <<'EOF'
import React from 'react'
export function Card({ children, className }: any) {
  return <div className={`border rounded-md p-4 bg-white dark:bg-gray-800 ${className || ''}`}>{children}</div>
}
export function CardHeader({ children }: any) {
  return <div className="mb-2 font-semibold border-b pb-1">{children}</div>
}
export function CardTitle({ children }: any) {
  return <h3 className="text-lg font-bold">{children}</h3>
}
export function CardContent({ children }: any) {
  return <div className="mb-2">{children}</div>
}
export function CardFooter({ children }: any) {
  return <div className="pt-2 border-t">{children}</div>
}
EOF

cat > src/components/ui/button.tsx <<'EOF'
import React from 'react'
export function Button({ children, size, type, ...props }: any) {
  const base = 'inline-block px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90'
  const sizeClass = size === 'sm' ? 'text-sm' : 'text-base'
  return <button type={type || 'button'} className={`${base} ${sizeClass}`} {...props}>{children}</button>
}
EOF

cat > src/components/ui/dialog.tsx <<'EOF'
export { Dialog, DialogTrigger, DialogContent, DialogTitle, DialogDescription, DialogClose } from '@radix-ui/react-dialog'
EOF

cat > src/components/ui/input.tsx <<'EOF'
import React from 'react'
export const Input = React.forwardRef(({ className, ...props }: any, ref) => {
  return <input ref={ref} className={`border rounded-md px-3 py-2 w-full ${className || ''}`} {...props} />
})
Input.displayName = 'Input'
EOF

cat > src/components/ui/checkbox.tsx <<'EOF'
export { Checkbox } from '@radix-ui/react-checkbox'
EOF

cat > src/components/ui/switch.tsx <<'EOF'
export { Switch } from '@radix-ui/react-switch'
EOF

# Run pnpm install to link local packages
pnpm install

cd ..

# Run bundle script to create bundle.html
bash scripts/bundle-artifact.sh

