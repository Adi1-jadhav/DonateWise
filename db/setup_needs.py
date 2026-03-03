from db.database import get_db_connection

def create_needs_table():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create ngo_needs table
    # category: The type of item (e.g., Food, Clothes)
    # item_name: Specific item (e.g., Rice, Winter Jackets)
    # quantity: How many units needed
    # priority: Low, Medium, High
    # status: Open, Fulfilled
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ngo_needs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ngo_id INT NOT NULL,
            category VARCHAR(50) NOT NULL,
            item_name VARCHAR(100) NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            description TEXT,
            priority ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
            status ENUM('Open', 'Fulfilled') DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ngo_id) REFERENCES ngos(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ ngo_needs table checked/created successfully.")

if __name__ == "__main__":
    create_needs_table()
