import React from 'react';
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from '@heroicons/react/24/solid';
import clsx from 'clsx';

interface MetricsCardProps {
    title: string;
    value: string | number;
    change?: number;
    changeType?: 'increase' | 'decrease' | 'neutral';
    icon?: React.ReactNode;
    description?: string;
    loading?: boolean;
    className?: string;
}

const MetricsCard: React.FC<MetricsCardProps> = ({
    title,
    value,
    change,
    changeType = 'neutral',
    icon,
    description,
    loading = false,
    className,
}) => {
    const getTrendIcon = () => {
        switch (changeType) {
            case 'increase':
                return <ArrowUpIcon className="h-4 w-4 text-green-500" />;
            case 'decrease':
                return <ArrowDownIcon className="h-4 w-4 text-red-500" />;
            default:
                return <MinusIcon className="h-4 w-4 text-gray-500" />;
        }
    };

    const getTrendColor = () => {
        switch (changeType) {
            case 'increase':
                return 'text-green-600';
            case 'decrease':
                return 'text-red-600';
            default:
                return 'text-gray-500';
        }
    };

    if (loading) {
        return (
            <div className={clsx('bg-white rounded-lg shadow-sm p-6', className)}>
                <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/4 mb-2"></div>
                </div>
            </div>
        );
    }

    return (
        <div className={clsx('bg-white rounded-lg shadow-sm p-6', className)}>
            <div className="flex items-center justify-between">
                <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">{title}</p>
                    <div ClassName="mt1 flex items-baseline">
                        <p className="text-2xl font-semibold text-gray-900">{value}</p>
                        {change !== undefined && (
                            <div className={clsx('ml-2 flex items-baseline text-sm', getTrendColor())}>
                                {getTrendIcon()}
                                <span className="ml-1">{Math.abs(change)}%</span>
                            </div>
                        )}
                    </div>
                    {description && (
                        <p className="mt-1 text-sm text-gray-500">{description}</p>
                    )}
                </div>
                {icon && (
                    <div className="flex-shrink-0">
                        {icon}
                    </div>
                )}
            </div>
        </div>
    );
};

export default MetricsCard;