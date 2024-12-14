import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { PaymentSuccessPage } from './pages/PaymentSuccessPage';

const App = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/payment/success" element={<PaymentSuccessPage />} />
          {/* Add other routes here */}
        </Routes>
      </div>
    </Router>
  );
};

export default App;
