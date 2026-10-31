pragma solidity 0.8.20;

contract Wallet3970 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        supply += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return supply; }

    function ownerOf_() public view returns (address) { return owner; }
}
