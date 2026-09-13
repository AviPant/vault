import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Shield, Lock } from 'lucide-react';
import VaultLogo from '../../VaultLogo';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Mock authentication check
    setTimeout(() => {
      if (username === 'admin' && password === 'vault2026') {
        onLogin(true);
      } else {
        setError('Invalid credentials. Air-gapped verification failed.');
        setLoading(false);
      }
    }, 800);
  };

  return (
    <div className="min-h-screen bg-surface-main flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-accent-teal/5 via-surface-main to-surface-main pointer-events-none"></div>
      
      <Card className="w-full max-w-md bg-surface/80 backdrop-blur-md border-muted/50 shadow-[0_0_40px_-15px_rgba(var(--accent-teal),0.1)] relative z-10 p-2 sm:p-4">
        <CardHeader className="space-y-4 pb-8">
          <div className="flex justify-center mb-4">
            <VaultLogo />
          </div>
          <CardTitle className="text-3xl font-jetbrains-mono text-center tracking-tight text-on-surface">V.A.U.L.T. Terminal</CardTitle>
          <CardDescription className="text-center text-text-dim text-xs font-jetbrains-mono uppercase tracking-widest mt-2">
            Sovereign AI Access Protocol
          </CardDescription>
        </CardHeader>
        
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-6">
            {error && (
              <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md flex items-start space-x-3">
                <Shield className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
                <p className="text-xs text-destructive font-jetbrains-mono leading-relaxed">{error}</p>
              </div>
            )}
            
            <div className="space-y-3">
              <Label htmlFor="username" className="text-xs font-jetbrains-mono text-on-surface-variant uppercase tracking-wider">Operator ID</Label>
              <Input 
                id="username" 
                type="text" 
                placeholder="Enter operator ID"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="h-11 bg-surface-main border-muted text-on-surface font-jetbrains-mono focus-visible:ring-accent-teal transition-all"
                required
              />
            </div>
            
            <div className="space-y-3">
              <Label htmlFor="password" className="text-xs font-jetbrains-mono text-on-surface-variant uppercase tracking-wider">Passcode</Label>
              <div className="relative">
                <Input 
                  id="password" 
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-11 bg-surface-main border-muted text-on-surface font-jetbrains-mono focus-visible:ring-accent-teal pl-10 transition-all"
                  required
                />
                <Lock className="w-4 h-4 text-text-dim absolute left-3.5 top-3.5" />
              </div>
            </div>
          </CardContent>
          
          <CardFooter className="pt-4">
            <Button 
              type="submit" 
              className="w-full h-12 bg-accent-teal hover:bg-accent-hover text-surface-main font-bold font-jetbrains-mono tracking-widest transition-all shadow-[0_0_20px_-5px_rgba(var(--accent-teal),0.4)]"
              disabled={loading}
            >
              {loading ? 'VERIFYING...' : 'INITIALIZE SESSION'}
            </Button>
          </CardFooter>
        </form>
      </Card>
      
      <div className="absolute bottom-6 text-center w-full">
        <p className="text-[10px] text-text-dim/40 font-jetbrains-mono uppercase tracking-widest">
          Mangalore Refinery and Petrochemicals Limited (MRPL)
        </p>
      </div>
    </div>
  );
}
