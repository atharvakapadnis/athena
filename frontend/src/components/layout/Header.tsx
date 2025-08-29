import React from 'react';

const Header: React.FC = () => {
  return (
    <div className="sticky top-0 z-40 lg:mx-auto lg:max-w-7xl lg:px-8">
      <div className="flex h-16 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-0 lg:shadow-none">
        <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
          <div className="relative flex flex-1">
            <div className="flex items-center">
              <h2 className="text-lg font-semibold text-gray-900">
                Smart Description System
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-x-4 lg:gap-x-6">
            <div className="text-sm text-gray-500">
              Internal Network Deployment
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;