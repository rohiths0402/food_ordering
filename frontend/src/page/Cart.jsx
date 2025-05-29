import React, { useEffect } from "react";
import CommonSection from "../component/UI/commonSelection/commonSelection";
import Helmet from "../component/Helmet";
import "../styles/cartPage.css";
import { useSelector, useDispatch } from "react-redux";
import { Container, Row, Col } from "reactstrap";
import { cartActions } from "../store/cartSlice";
import { Link } from "react-router-dom";

const Cart = () => {
  const cartItems = useSelector((state) => state.cart.cartItems);
  const totalAmount = useSelector((state) => state.cart.totalAmount);
  const dispatch = useDispatch();

  // Get JWT token from localStorage
  const token = localStorage.getItem("token");

  // Sync full cart to backend on every cartItems change
  useEffect(() => {
    const syncCartToBackend = async () => {
      try {
        const response = await fetch("http://localhost:5000/cart", {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ cartItems }),
        });

        if (!response.ok) {
          throw new Error("Failed to sync cart with backend");
        }

        const data = await response.json();
        console.log("Cart synced with backend:", data);
      } catch (error) {
        console.error("Error syncing cart:", error);
      }
    };

    if (cartItems.length > 0) {
      syncCartToBackend();
    }
  }, [cartItems, token]);

  // Delete item only locally from Redux store
  const handleDelete = (id) => {
    dispatch(cartActions.deleteItem(id));
  };

  return (
    <Helmet title="Cart">
      <CommonSection title="Your Cart" />
      <section>
        <Container>
          <Row>
            <Col lg="12">
              {cartItems.length === 0 ? (
                <h5 className="text-center">Your cart is empty</h5>
              ) : (
                <table className="table table-bordered">
                  <thead>
                    <tr>
                      <th>Image</th>
                      <th>Product Title</th>
                      <th>Price</th>
                      <th>Quantity</th>
                      <th>Delete</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cartItems.map((item) => (
                      <Tr
                        key={item.id}
                        item={item}
                        onDelete={() => handleDelete(item.id)}
                      />
                    ))}
                  </tbody>
                </table>
              )}

              <div className="mt-4">
                <h6>
                  Subtotal: $
                  <span className="cart__subtotal">{totalAmount}</span>
                </h6>
                <p>Taxes and shipping will calculate at checkout</p>
                <div className="cart__page-btn">
                  <button className="addTOCart__btn me-4">
                    <Link to="/foods">Continue Shopping</Link>
                  </button>
                  {(localStorage.getItem("role") === "admin" ||
                    localStorage.getItem("role") === "manager") && (
                    <button className="addTOCart__btn">
                      <Link to="/checkout">Proceed to checkout</Link>
                    </button>
                  )}
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </section>
    </Helmet>
  );
};

const Tr = ({ item, onDelete }) => {
  const { image01, title, price, quantity } = item;

  return (
    <tr>
      <td className="text-center cart__img-box">
        <img src={image01} alt={title} />
      </td>
      <td className="text-center">{title}</td>
      <td className="text-center">${price}</td>
      <td className="text-center">{quantity}</td>
      <td className="text-center cart__item-del">
        <i
          className="ri-delete-bin-line"
          onClick={onDelete}
          style={{ cursor: "pointer" }}
        ></i>
      </td>
    </tr>
  );
};

export default Cart;
