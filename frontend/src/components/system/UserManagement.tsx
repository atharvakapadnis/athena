import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PlusIcon, UserIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import { systemAPI } from '../../services/systemAPI';
import { UserRequest } from '../../types/system';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Modal from '../ui/Modal';

const UserManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUser, setNewUser] = useState<UserRequest>({
    username: '',
    email: '',
    role: 'user'
  });

  const { data: users, isLoading } = useQuery({
    queryKey: ['system', 'users'],
    queryFn: systemAPI.getUsers,
  });

  const createUserMutation = useMutation({
    mutationFn: (user: UserRequest) => systemAPI.createUser(user),
    onSuccess: () => {
      toast.success('User created successfully');
      setShowCreateUser(false);
      setNewUser({ username: '', email: '', role: 'user' });
      queryClient.invalidateQueries(['system', 'users']);
    },
    onError: (error: any) => {
      toast.error(`Failed to create user: ${error.message}`);
    }
  });

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault();
    createUserMutation.mutate(newUser);
  };

  const usersList = users?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
        <Button onClick={() => setShowCreateUser(true)}>
          <PlusIcon className="w-4 h-4 mr-2" />
          Add User
        </Button>
      </div>

      {/* Internal Network Notice */}
      <Card className="p-4 bg-blue-50 border-blue-200">
        <div className="flex items-center space-x-2">
          <UserIcon className="w-5 h-5 text-blue-500" />
          <div>
            <h4 className="text-sm font-medium text-blue-800">Internal Network Users</h4>
            <p className="text-sm text-blue-600">
              User management is simplified for internal network deployment. 
              All users have trusted network access with role-based permissions.
            </p>
          </div>
        </div>
      </Card>

      {/* Users List */}
      <Card className="overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            System Users ({usersList.length})
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Login
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
            {usersList.map((user) => (
               <tr key={user.username} className="hover:bg-gray-50">
                 <td className="px-6 py-4 whitespace-nowrap">
                   <div className="flex items-center">
                     <div className="flex-shrink-0">
                       <UserIcon className="w-8 h-8 text-gray-400" />
                     </div>
                     <div className="ml-3">
                       <div className="text-sm font-medium text-gray-900">
                         {user.username}
                       </div>
                     </div>
                   </div>
                 </td>
                 <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                   {user.email}
                 </td>
                 <td className="px-6 py-4 whitespace-nowrap">
                   <span className={`
                     inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
                     ${user.role === 'admin' 
                       ? 'text-purple-700 bg-purple-100' 
                       : 'text-gray-700 bg-gray-100'}
                   `}>
                     {user.role}
                   </span>
                 </td>
                 <td className="px-6 py-4 whitespace-nowrap">
                   <span className={`
                     inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
                     ${user.active 
                       ? 'text-green-700 bg-green-100' 
                       : 'text-red-700 bg-red-100'}
                   `}>
                     {user.active ? 'Active' : 'Inactive'}
                   </span>
                 </td>
                 <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                   {user.last_login 
                     ? new Date(user.last_login).toLocaleDateString()
                     : 'Never'
                   }
                 </td>
               </tr>
             ))}
           </tbody>
         </table>

         {usersList.length === 0 && !isLoading && (
           <div className="text-center py-12">
             <UserIcon className="mx-auto h-12 w-12 text-gray-400" />
             <h3 className="mt-2 text-sm font-medium text-gray-900">No users found</h3>
             <p className="mt-1 text-sm text-gray-500">
               Get started by creating the first user.
             </p>
           </div>
         )}
       </div>
     </Card>

     {/* Create User Modal */}
     <Modal
       isOpen={showCreateUser}
       onClose={() => setShowCreateUser(false)}
       title="Create New User"
     >
       <form onSubmit={handleCreateUser} className="space-y-4">
         <div>
           <label className="block text-sm font-medium text-gray-700">
             Username
           </label>
           <input
             type="text"
             required
             value={newUser.username}
             onChange={(e) => setNewUser(prev => ({ ...prev, username: e.target.value }))}
             className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
             placeholder="Enter username"
           />
         </div>

         <div>
           <label className="block text-sm font-medium text-gray-700">
             Email
           </label>
           <input
             type="email"
             required
             value={newUser.email}
             onChange={(e) => setNewUser(prev => ({ ...prev, email: e.target.value }))}
             className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
             placeholder="Enter email address"
           />
         </div>

         <div>
           <label className="block text-sm font-medium text-gray-700">
             Role
           </label>
           <select
             value={newUser.role}
             onChange={(e) => setNewUser(prev => ({ ...prev, role: e.target.value }))}
             className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
           >
             <option value="user">User</option>
             <option value="admin">Admin</option>
             <option value="viewer">Viewer</option>
           </select>
         </div>

         <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
           <Button
             type="button"
             variant="outline"
             onClick={() => setShowCreateUser(false)}
           >
             Cancel
           </Button>
           <Button
             type="submit"
             loading={createUserMutation.isLoading}
           >
             Create User
           </Button>
         </div>
       </form>
     </Modal>
   </div>
 );
};

export default UserManagement;