pragma solidity 0.5.12;

contract Ledger5373 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        total += msg.value;
    }

    function balanceOf(address who) public view returns (uint256) { return credit[who]; }

    function ownerOf_() public view returns (address) { return owner; }
}
