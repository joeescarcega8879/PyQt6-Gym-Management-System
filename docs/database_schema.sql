-- ============================================
-- SISTEMA DE GESTIÓN DE GIMNASIO - SCHEMA SQL
-- Base de datos: PostgreSQL (Supabase)
-- ============================================

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLA: users (Usuarios del sistema)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'receptionist', 'instructor', 'accountant')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: members (Miembros del gimnasio)
-- ============================================
CREATE TABLE members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_code VARCHAR(20) UNIQUE NOT NULL, -- Código de barras/QR
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    address TEXT,
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    photo_url TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- ============================================
-- TABLA: membership_plans (Planes de membresía)
-- ============================================
CREATE TABLE membership_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    duration_days INTEGER NOT NULL, -- Duración en días (30, 90, 365, etc.)
    price DECIMAL(10, 2) NOT NULL,
    has_class_access BOOLEAN DEFAULT true,
    max_classes_per_week INTEGER, -- NULL = ilimitado
    features JSONB, -- Características adicionales en formato JSON
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: member_memberships (Membresías activas de miembros)
-- ============================================
CREATE TABLE member_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    membership_plan_id UUID NOT NULL REFERENCES membership_plans(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'expired', 'suspended', 'cancelled')),
    auto_renew BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- ============================================
-- TABLA: payments (Pagos)
-- ============================================
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL REFERENCES members(id),
    membership_id UUID REFERENCES member_memberships(id),
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('cash', 'card', 'transfer', 'other')),
    payment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL CHECK (status IN ('completed', 'pending', 'cancelled', 'refunded')),
    reference_number VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- ============================================
-- TABLA: attendance (Asistencia/Check-ins)
-- ============================================
CREATE TABLE attendance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL REFERENCES members(id),
    check_in_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    check_out_time TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_by UUID REFERENCES users(id)
);

-- ============================================
-- TABLA: instructors (Instructores)
-- ============================================
CREATE TABLE instructors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id), -- Si el instructor también es usuario del sistema
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    specialties TEXT[], -- Array de especialidades
    certifications TEXT,
    hire_date DATE,
    photo_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: classes (Clases grupales)
-- ============================================
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    duration_minutes INTEGER NOT NULL,
    max_capacity INTEGER,
    difficulty_level VARCHAR(20) CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced', 'all')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: class_schedules (Horarios de clases)
-- ============================================
CREATE TABLE class_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id UUID NOT NULL REFERENCES classes(id),
    instructor_id UUID REFERENCES instructors(id),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Domingo, 6=Sábado
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: class_enrollments (Inscripciones a clases)
-- ============================================
CREATE TABLE class_enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schedule_id UUID NOT NULL REFERENCES class_schedules(id),
    member_id UUID NOT NULL REFERENCES members(id),
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL CHECK (status IN ('enrolled', 'attended', 'absent', 'cancelled')),
    class_date DATE NOT NULL, -- Fecha específica de la clase
    notes TEXT,
    UNIQUE(schedule_id, member_id, class_date)
);

-- ============================================
-- TABLA: equipment (Equipamiento/Inventario)
-- ============================================
CREATE TABLE equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    brand VARCHAR(50),
    model VARCHAR(50),
    serial_number VARCHAR(100),
    purchase_date DATE,
    purchase_price DECIMAL(10, 2),
    condition VARCHAR(20) CHECK (condition IN ('excellent', 'good', 'fair', 'poor', 'out_of_service')),
    location VARCHAR(100),
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: equipment_maintenance (Mantenimiento de equipamiento)
-- ============================================
CREATE TABLE equipment_maintenance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id UUID NOT NULL REFERENCES equipment(id),
    maintenance_date DATE NOT NULL,
    maintenance_type VARCHAR(50) NOT NULL CHECK (maintenance_type IN ('preventive', 'corrective', 'inspection')),
    description TEXT,
    cost DECIMAL(10, 2),
    performed_by VARCHAR(100),
    next_maintenance_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- ============================================
-- TABLA: cash_register (Movimientos de caja)
-- ============================================
CREATE TABLE cash_register (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opening_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closing_date TIMESTAMP WITH TIME ZONE,
    opening_amount DECIMAL(10, 2) NOT NULL,
    closing_amount DECIMAL(10, 2),
    expected_amount DECIMAL(10, 2),
    difference DECIMAL(10, 2),
    status VARCHAR(20) NOT NULL CHECK (status IN ('open', 'closed')),
    notes TEXT,
    opened_by UUID REFERENCES users(id),
    closed_by UUID REFERENCES users(id)
);

-- ============================================
-- TABLA: notifications (Notificaciones)
-- ============================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN ('membership_expiring', 'membership_expired', 'birthday', 'payment_reminder', 'system', 'custom')),
    member_id UUID REFERENCES members(id),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    scheduled_date TIMESTAMP WITH TIME ZONE,
    sent_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: audit_log (Registro de auditoría)
-- ============================================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL, -- CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    table_name VARCHAR(50),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- ÍNDICES para mejorar performance
-- ============================================

-- Índices para búsquedas frecuentes
CREATE INDEX idx_members_member_code ON members(member_code);
CREATE INDEX idx_members_email ON members(email);
CREATE INDEX idx_members_is_active ON members(is_active);
CREATE INDEX idx_members_created_at ON members(created_at);

CREATE INDEX idx_attendance_member_id ON attendance(member_id);
CREATE INDEX idx_attendance_check_in_time ON attendance(check_in_time);

CREATE INDEX idx_payments_member_id ON payments(member_id);
CREATE INDEX idx_payments_payment_date ON payments(payment_date);
CREATE INDEX idx_payments_status ON payments(status);

CREATE INDEX idx_member_memberships_member_id ON member_memberships(member_id);
CREATE INDEX idx_member_memberships_status ON member_memberships(status);
CREATE INDEX idx_member_memberships_end_date ON member_memberships(end_date);

CREATE INDEX idx_class_enrollments_member_id ON class_enrollments(member_id);
CREATE INDEX idx_class_enrollments_schedule_id ON class_enrollments(schedule_id);
CREATE INDEX idx_class_enrollments_class_date ON class_enrollments(class_date);

CREATE INDEX idx_notifications_member_id ON notifications(member_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_scheduled_date ON notifications(scheduled_date);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- ============================================
-- TRIGGERS para actualizar updated_at
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger a las tablas necesarias
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_members_updated_at BEFORE UPDATE ON members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_membership_plans_updated_at BEFORE UPDATE ON membership_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_member_memberships_updated_at BEFORE UPDATE ON member_memberships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_instructors_updated_at BEFORE UPDATE ON instructors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_classes_updated_at BEFORE UPDATE ON classes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_class_schedules_updated_at BEFORE UPDATE ON class_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_equipment_updated_at BEFORE UPDATE ON equipment
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- DATOS INICIALES (SEED DATA)
-- ============================================

-- Usuario administrador por defecto (contraseña: admin123)
-- NOTA: Cambiar la contraseña en producción
INSERT INTO users (username, email, password_hash, full_name, role) VALUES
('admin', 'admin@gym.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqKm5Pg7aG', 'Administrador del Sistema', 'admin');

-- Planes de membresía de ejemplo
INSERT INTO membership_plans (name, description, duration_days, price, has_class_access) VALUES
('Mensual Básico', 'Acceso al gimnasio por 30 días', 30, 500.00, false),
('Mensual Premium', 'Acceso al gimnasio y clases grupales ilimitadas', 30, 800.00, true),
('Trimestral Premium', 'Acceso completo por 90 días con descuento', 90, 2100.00, true),
('Anual Premium', 'Acceso completo por 1 año con mejor precio', 365, 7200.00, true);

-- ============================================
-- COMENTARIOS EN TABLAS
-- ============================================

COMMENT ON TABLE users IS 'Usuarios del sistema (admin, recepcionista, instructor, contador)';
COMMENT ON TABLE members IS 'Miembros/clientes del gimnasio';
COMMENT ON TABLE membership_plans IS 'Planes de membresía disponibles';
COMMENT ON TABLE member_memberships IS 'Membresías activas de cada miembro';
COMMENT ON TABLE payments IS 'Registro de todos los pagos';
COMMENT ON TABLE attendance IS 'Control de asistencia (check-in/check-out)';
COMMENT ON TABLE instructors IS 'Instructores del gimnasio';
COMMENT ON TABLE classes IS 'Tipos de clases grupales disponibles';
COMMENT ON TABLE class_schedules IS 'Horarios de clases semanales';
COMMENT ON TABLE class_enrollments IS 'Inscripciones de miembros a clases específicas';
COMMENT ON TABLE equipment IS 'Inventario de equipamiento';
COMMENT ON TABLE equipment_maintenance IS 'Historial de mantenimiento de equipamiento';
COMMENT ON TABLE cash_register IS 'Control de apertura y cierre de caja';
COMMENT ON TABLE notifications IS 'Notificaciones y recordatorios automáticos';
COMMENT ON TABLE audit_log IS 'Registro de auditoría del sistema';
