import express from 'express';
import axios from 'axios';
import dotenv from 'dotenv';
import base64 from 'base-64';

dotenv.config();

const router = express.Router();

const TEKMETRICS_API_URL = process.env.TEKMETRICS_API_BASE_URL;
const SHOP_ID = process.env.SHOP_ID;
const CLIENT_ID = process.env.TEKMETRICS_CLIENT_ID;
const CLIENT_SECRET = process.env.TEKMETRICS_CLIENT_SECRET;
const TOKEN_URL = `${TEKMETRICS_API_URL}/oauth/token`;

const getAccessToken = async () => {
  const authHeader = `${CLIENT_ID}:${CLIENT_SECRET}`;
  const base64Auth = base64.encode(authHeader);

  try {
    const response = await axios.post(
      TOKEN_URL,
      'grant_type=client_credentials',
      {
        headers: {
          Authorization: `Basic ${base64Auth}`,
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        },
      }
    );
    return response.data.access_token;
  } catch (error) {
    console.error('Failed to obtain access token:', error);
    return null;
  }
};

const fetchData = async (url, headers) => {
  try {
    const response = await axios.get(url, { headers });
    console.log(`Data fetched from ${url}:`, response.data); // Log the fetched data
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch data from ${url}:`, error);
    return null;
  }
};

router.get('/customer/:customerId', async (req, res) => {
  const customerId = req.params.customerId;
  const accessToken = await getAccessToken();

  if (!accessToken) {
    return res.status(500).json({ error: 'Failed to obtain access token' });
  }

  const headers = {
    Authorization: `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  };

  const customerUrl = `${TEKMETRICS_API_URL}/customers/${customerId}?shop=${SHOP_ID}`;
  const customerData = await fetchData(customerUrl, headers);

  if (!customerData) {
    return res.status(404).json({ error: 'Customer not found' });
  }

  const repairOrdersUrl = `${TEKMETRICS_API_URL}/repair-orders?shop=${SHOP_ID}&customerId=${customerId}`;
  const repairOrdersData = await fetchData(repairOrdersUrl, headers);

  console.log('Repair Orders Data:', repairOrdersData); // Log the response to verify format

  if (!repairOrdersData) {
    return res.status(500).json({ error: 'Error fetching repair orders' });
  }

  return res.json({
    customer: customerData,
    repair_orders: repairOrdersData.content,
  });
});

// New route to search customer by email
router.get('/search', async (req, res) => {
  const email = req.query.email;
  const accessToken = await getAccessToken();

  if (!accessToken) {
    return res.status(500).json({ error: 'Failed to obtain access token' });
  }

  const headers = {
    Authorization: `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  };

  const searchUrl = `${TEKMETRICS_API_URL}/customers?shop=${SHOP_ID}&search=${email}`;
  const searchData = await fetchData(searchUrl, headers);

  if (!searchData || !searchData.content || searchData.content.length === 0) {
    return res.status(404).json({ error: 'Customer not found' });
  }

  const customerId = searchData.content[0].id;

  const customerUrl = `${TEKMETRICS_API_URL}/customers/${customerId}?shop=${SHOP_ID}`;
  const customerData = await fetchData(customerUrl, headers);

  const repairOrdersUrl = `${TEKMETRICS_API_URL}/repair-orders?shop=${SHOP_ID}&customerId=${customerId}`;
  const repairOrdersData = await fetchData(repairOrdersUrl, headers);

  return res.json({
    customer: customerData,
    repair_orders: repairOrdersData ? repairOrdersData.content : []
  });
});

export default router;
