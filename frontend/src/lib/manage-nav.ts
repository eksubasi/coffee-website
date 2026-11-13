import {
  BarChart3,
  FileText,
  FolderTree,
  Headset,
  LayoutDashboard,
  MessageSquareText,
  Package,
  Percent,
  Truck,
  Undo2,
  type LucideIcon,
} from 'lucide-react'

import type { Role } from '@/lib/auth'

/** Roles that may enter /manage. Customers are redirected back to the store (KAN-49). */
export type StaffRole = Exclude<Role, 'customer'>
export const STAFF_ROLES: StaffRole[] = ['product_manager', 'sales_manager', 'support_agent']

export const ROLE_LABELS: Record<StaffRole, string> = {
  product_manager: 'Product manager',
  sales_manager: 'Sales manager',
  support_agent: 'Support agent',
}

export function isStaff(role: Role | undefined): role is StaffRole {
  return role !== undefined && (STAFF_ROLES as Role[]).includes(role)
}

export interface ManageSection {
  /** Path under /manage, e.g. "products" -> /manage/products. */
  path: string
  label: string
  icon: LucideIcon
  roles: StaffRole[]
  /** Short description for the overview cards. */
  description: string
  /** Jira ticket that builds the page; until then the route shows a placeholder. */
  ticket: string
}

/**
 * Single source of truth for the manager area: the sidebar menu, the overview cards and the
 * route guards are all generated from this list (Req 8, 11, 12, 13).
 */
export const MANAGE_SECTIONS: ManageSection[] = [
  // Product manager (Req 12)
  {
    path: 'products',
    label: 'Products',
    icon: Package,
    roles: ['product_manager'],
    description: 'Add, edit and remove products.',
    ticket: 'KAN-50',
  },
  {
    path: 'categories',
    label: 'Categories & stock',
    icon: FolderTree,
    roles: ['product_manager'],
    description: 'Manage categories and update stock levels.',
    ticket: 'KAN-59',
  },
  {
    path: 'deliveries',
    label: 'Deliveries',
    icon: Truck,
    roles: ['product_manager'],
    description: 'Track deliveries and update order status.',
    ticket: 'KAN-60',
  },
  {
    path: 'comments',
    label: 'Comments',
    icon: MessageSquareText,
    roles: ['product_manager'],
    description: 'Approve or reject customer reviews.',
    ticket: 'KAN-61',
  },
  // Shared: both managers can see invoices
  {
    path: 'invoices',
    label: 'Invoices',
    icon: FileText,
    roles: ['product_manager', 'sales_manager'],
    description: 'Browse invoices and open their PDFs.',
    ticket: 'KAN-61 / KAN-80',
  },
  // Sales manager (Req 11)
  {
    path: 'sales',
    label: 'Pricing & discounts',
    icon: Percent,
    roles: ['sales_manager'],
    description: 'Set prices and run discounts.',
    ticket: 'KAN-80',
  },
  {
    path: 'revenue',
    label: 'Revenue & profit',
    icon: BarChart3,
    roles: ['sales_manager'],
    description: 'Revenue and profit/loss between two dates.',
    ticket: 'KAN-80',
  },
  {
    path: 'refunds',
    label: 'Returns & refunds',
    icon: Undo2,
    roles: ['sales_manager'],
    description: 'Review return requests and approve refunds.',
    ticket: 'Req 16',
  },
  // Support agent (Req 13)
  {
    path: 'support',
    label: 'Support chats',
    icon: Headset,
    roles: ['support_agent'],
    description: 'Claim conversations from the queue and reply.',
    ticket: 'KAN-117',
  },
]

export const OVERVIEW_ICON = LayoutDashboard

export function sectionsFor(role: Role | undefined): ManageSection[] {
  return isStaff(role) ? MANAGE_SECTIONS.filter((s) => s.roles.includes(role)) : []
}
