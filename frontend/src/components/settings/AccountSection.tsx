import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function AccountSection() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Account</CardTitle>
        <CardDescription>
          Manage your profile, security, and billing preferences.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border p-4 space-y-2">
          <p className="text-sm font-medium">Profile</p>
          <p className="text-xs text-muted-foreground">
            Update your name, avatar, and contact details.
          </p>
          <Button variant="outline" size="sm" disabled>
            Manage profile
          </Button>
        </div>
        <div className="rounded-lg border p-4 space-y-2">
          <p className="text-sm font-medium">Security</p>
          <p className="text-xs text-muted-foreground">
            Passwords, sessions, and device access.
          </p>
          <Button variant="outline" size="sm" disabled>
            Review security
          </Button>
        </div>
        <div className="rounded-lg border p-4 space-y-2 md:col-span-2">
          <p className="text-sm font-medium">Billing</p>
          <p className="text-xs text-muted-foreground">
            Subscription details and invoices will appear here soon.
          </p>
          <Button variant="outline" size="sm" disabled>
            Open billing portal
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
