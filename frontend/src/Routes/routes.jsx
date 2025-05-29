import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import Home from "../page/Home";
import AllFoods from "../page/Allfood";
import FoodDetails from "../page/FoodDetails";
import Cart from "../page/Cart";
import Checkout from "../page/checkout";
import Contact from "../page/contact";
import Login from "../page/login";

const Routers = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/home" element={<Home />} />
      <Route path="/foods" element={<AllFoods />} />
      <Route path="/foods/:id" element={<FoodDetails />} />
      <Route path="/cart" element={<Cart />} />
      <Route path="/checkout" element={<Checkout />} />
      <Route path="/login" element={<Login />} />
      <Route path="/contact" element={<Contact />} />
    </Routes>
  );
};

export default Routers;
