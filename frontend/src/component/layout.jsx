import Header from "./header.jsx";
import Footer from "./footer.jsx";
import Routers from "../Routes/routes.jsx"; 
import Carts from "./UI/cart/carts.jsx";
import { useSelector } from "react-redux";

const Layout = () => {
  const showCart = useSelector((state) => state.cartUi.cartIsVisible);
  return (
    <div>
      <Header />
      {showCart && <Carts />}
      <div>
        <Routers /> {/* ✅ Use the correct component name */}
      </div>
      <Footer />
    </div>
  );
};

export default Layout;
