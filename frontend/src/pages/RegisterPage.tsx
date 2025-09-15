import { RegisterForm } from '@/components/auth/RegisterForm';
import { usePageTitle } from '@/hooks/use-page-title';

export function RegisterPage() {
    usePageTitle('Register');
    return <RegisterForm />;
}