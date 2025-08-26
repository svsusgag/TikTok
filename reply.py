import base64
import cv2
import numpy as np


class PuzzleSolver:
    def __init__(self, base64puzzle, base64piece):
        self.puzzle = base64puzzle
        self.piece = base64piece
        self.methods = [
            cv2.TM_CCOEFF_NORMED,
            cv2.TM_CCORR_NORMED
        ]

    def get_position(self):
        try:
            results = []

            puzzle = self.__background_preprocessing()
            piece = self.__piece_preprocessing()

            for method in self.methods:
                matched = cv2.matchTemplate(puzzle, piece, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matched)
                if method == cv2.TM_SQDIFF_NORMED:
                    results.append((min_loc[0], 1 - min_val))
                else:
                    results.append((max_loc[0], max_val))

            enhanced_puzzle = self.__enhanced_preprocessing(puzzle)
            enhanced_piece = self.__enhanced_preprocessing(piece)

            for method in self.methods:
                matched = cv2.matchTemplate(enhanced_puzzle, enhanced_piece, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matched)
                if method == cv2.TM_SQDIFF_NORMED:
                    results.append((min_loc[0], 1 - min_val))
                else:
                    results.append((max_loc[0], max_val))

            edge_puzzle = self.__edge_detection(puzzle)
            edge_piece = self.__edge_detection(piece)

            matched = cv2.matchTemplate(edge_puzzle, edge_piece, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matched)
            results.append((max_loc[0], max_val))

            results.sort(key=lambda x: x[1], reverse=True)
            return results[0][0]

        except Exception as e:
            puzzle = self.__background_preprocessing()
            piece = self.__piece_preprocessing()
            matched = cv2.matchTemplate(puzzle, piece, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matched)
            return max_loc[0]

    def __background_preprocessing(self):
        img = self.__img_to_array(self.piece)
        background = self.__sobel_operator(img)
        return background

    def __piece_preprocessing(self):
        img = self.__img_to_array(self.puzzle)
        template = self.__sobel_operator(img)
        return template

    def __enhanced_preprocessing(self, img):
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(img)

        return enhanced

    def __edge_detection(self, img):
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        edges = cv2.Canny(blurred, 50, 150)

        return edges

    def __sobel_operator(self, img):
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        grad_x = cv2.Sobel(gray, cv2.CV_16S, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_16S, 0, 1, ksize=3)

        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)

        grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

        grad = cv2.normalize(grad, None, 0, 255, cv2.NORM_MINMAX)

        return grad

    def __img_to_array(self, base64_input):
        try:
            img_data = base64.b64decode(base64_input)
            img_array = np.frombuffer(img_data, dtype=np.uint8)

            decoded_img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)

            if decoded_img is None:
                raise ValueError("Failed to decode image")

            if len(decoded_img.shape) == 2:
                decoded_img = cv2.cvtColor(decoded_img, cv2.COLOR_GRAY2BGR)
            elif decoded_img.shape[2] == 4:
                decoded_img = cv2.cvtColor(decoded_img, cv2.COLOR_RGBA2BGR)

            return decoded_img

        except Exception as e:
            raise ValueError(f"Image processing error: {str(e)}")

