import { LoginForm } from '@/components/auth/LoginForm';
import { usePageTitle } from '@/hooks/use-page-title';

export function LoginPage() {
    usePageTitle('Login');
    return <LoginForm />;
}