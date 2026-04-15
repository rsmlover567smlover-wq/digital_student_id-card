import qrcode
from pyzbar.pyzbar import decode
import cv2
from PIL import Image
import os

def generate_qr(data: str, filename: str = "my_qr_code.png"):
    """Generate a QR code and save it as an image"""
    # Create QR code
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR code
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image
    img.save(filename)
    print(f"✅ QR Code generated and saved as '{filename}'")
    print(f"   Data encoded: {data}")
    
    # Optional: Open the image automatically
    img.show()  # Opens with default image viewer


def scan_qr_from_image(image_path: str):
    """Scan QR code from an image file"""
    if not os.path.exists(image_path):
        print("❌ Image file not found!")
        return None
    
    # Read the image
    img = Image.open(image_path)
    
    # Decode QR codes
    decoded_objects = decode(img)
    
    if not decoded_objects:
        print("❌ No QR code found in the image!")
        return None
    
    for obj in decoded_objects:
        qr_data = obj.data.decode('utf-8')
        qr_type = obj.type
        print(f"✅ QR Code detected!")
        print(f"   Type: {qr_type}")
        print(f"   Data: {qr_data}")
        return qr_data  # Return the first one found


def scan_qr_from_camera():
    """Real-time QR code scanner using webcam"""
    print("📷 Starting QR Code Scanner (Press 'q' to quit)")
    cap = cv2.VideoCapture(0)  # 0 = default camera
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame")
            break
        
        # Decode QR codes in the current frame
        decoded_objects = decode(frame)
        
        for obj in decoded_objects:
            # Get the data
            qr_data = obj.data.decode('utf-8')
            
            # Draw rectangle around QR code
            (x, y, w, h) = obj.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
            
            # Display the data on the frame
            cv2.putText(frame, qr_data, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            print(f"✅ Scanned: {qr_data}")
        
        # Show the frame
        cv2.imshow("QR Code Scanner - Press 'q' to quit", frame)
        
        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


# ========================
# Main Menu
# ========================
if __name__ == "__main__":
    print("🔹 QR Code Generator & Scanner 🔹\n")
    
    while True:
        print("\nChoose an option:")
        print("1. Generate QR Code")
        print("2. Scan QR Code from Image")
        print("3. Live Camera QR Scanner")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            data = input("Enter data/text/URL to encode: ").strip()
            if data:
                filename = input("Enter filename (default: my_qr_code.png): ").strip() or "my_qr_code.png"
                generate_qr(data, filename)
                
        elif choice == "2":
            path = input("Enter image path (e.g., my_qr_code.png): ").strip()
            scan_qr_from_image(path)
            
        elif choice == "3":
            scan_qr_from_camera()
            
        elif choice == "4":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice! Please try again.")