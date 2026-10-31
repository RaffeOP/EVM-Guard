pragma solidity 0.8.20;

contract Escrow2367 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        supply += msg.value;
    }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }

    function ownerOf_() public view returns (address) { return owner; }
}
