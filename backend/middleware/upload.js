import multer from "multer";

// Changed: enforce in-memory storage but add file size limits and an image-only filter
const storage = multer.memoryStorage();

const fileFilter = (req, file, cb) => {
	// Accept only images
	if (file.mimetype && file.mimetype.startsWith("image/")) {
		cb(null, true);
	} else {
		cb(new Error("Only image files are allowed"), false);
	}
};

const upload = multer({
	storage,
	limits: { fileSize: 5 * 1024 * 1024 }, // 5MB max
	fileFilter,
});

export default upload;